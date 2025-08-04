import os
from typing import List, Dict, Any
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from dotenv import load_dotenv
import json

load_dotenv()

class RAGService:
    def __init__(self):
        # Set up persistent directory
        curr_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.persistent_dir = os.path.join(curr_dir, "db", "vector_store")
        self.jd_collection_name = "job_descriptions"
        self.resume_collection_name = "resumes"
        
        # Ensure directory exists
        os.makedirs(self.persistent_dir, exist_ok=True)
        
        # Check if Azure OpenAI environment variables are set
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        # Debug logging
        print(f"🔍 Environment variables check:")
        print(f"  API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
        print(f"  ENDPOINT: {'✅ Set' if endpoint else '❌ Missing'}")
        print(f"  DEPLOYMENT: {'✅ Set' if deployment else '❌ Missing'}")
        print(f"  EMBEDDING_DEPLOYMENT: {'✅ Set' if embedding_deployment else '❌ Missing'}")
        print(f"  API_VERSION: {'✅ Set' if api_version else '❌ Missing'}")
        
        self.azure_configured = all([api_key, endpoint, deployment, embedding_deployment, api_version])
        
        if not self.azure_configured:
            print("⚠️  Azure OpenAI not configured. RAG features will be disabled.")
            print("Please set the following environment variables:")
            print("- AZURE_OPENAI_API_KEY")
            print("- AZURE_OPENAI_ENDPOINT") 
            print("- AZURE_OPENAI_DEPLOYMENT_NAME")
            print("- AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
            print("- AZURE_OPENAI_API_VERSION")
            self.model = None
            self.embeddings = None
            self.jd_vector_store = None
            self.resume_vector_store = None
            self.text_splitter = None
            self.matching_prompt = None
            return
        
        # Initialize LLM and Embeddings
        try:
            self.model = AzureChatOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION")
            )
            
            self.embeddings = AzureOpenAIEmbeddings(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_deployment=embedding_deployment,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                model=embedding_deployment
            )
            
            # Initialize vector stores
            self.jd_vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persistent_dir,
                collection_name=self.jd_collection_name
            )
            
            self.resume_vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persistent_dir,
                collection_name=self.resume_collection_name
            )
            
            # Text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # Prompt template for matching
            self.matching_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert HR professional and technical recruiter specializing in tech hiring.
                
                TASK: Analyze the match between a candidate's resume and a job description.
                
                RESUME: {resume_content}
                
                JOB DESCRIPTION: {jd_content}
                
                ANALYSIS CRITERIA:
                1. Technical Skills Match (40% weight)
                2. Experience Level Alignment (30% weight) 
                3. Required Qualifications vs. Possessed (20% weight)
                4. Overall Role Fit (10% weight)
                
                INSTRUCTIONS:
                - Be strict and objective in your assessment
                - Only give high match percentages (80%+) for excellent fits
                - Focus on concrete skills and experience, not generic statements
                - Identify specific missing skills that are critical for the role
                
                RESPONSE FORMAT (JSON only):
                {{
                    "match_percentage": <number between 0-100>,
                    "analysis": "<detailed analysis explaining the match score>",
                    "key_matches": ["<specific skill 1>", "<specific skill 2>", ...],
                    "missing_skills": ["<critical missing skill 1>", "<critical missing skill 2>", ...],
                    "recommendations": "<specific recommendations for improvement>"
                }}
                
                IMPORTANT: Only return valid JSON. No additional text."""),
                ("user", "Analyze the match between this resume and job description. Return only JSON.")
            ])
            
            # Auto-initialize job descriptions
            self.load_job_descriptions()
            print("✅ RAG system initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing RAG system: {str(e)}")
            self.azure_configured = False
            self.model = None
            self.embeddings = None
            self.jd_vector_store = None
            self.resume_vector_store = None
            self.text_splitter = None
            self.matching_prompt = None
    
    def load_job_descriptions(self):
        """Load all job descriptions from the jd folder into the vector store"""
        if not self.azure_configured:
            print("⚠️  Cannot load job descriptions: Azure OpenAI not configured")
            return
            
        jd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jd")
        
        if not os.path.exists(jd_dir):
            print("JD directory not found")
            return
        
        # Clear existing JD documents
        try:
            self.jd_vector_store._collection.delete(where={"type": "job_description"})
        except Exception as e:
            print(f"Warning: Could not clear existing JDs: {e}")
            # Fallback: try to delete all documents
            try:
                self.jd_vector_store._collection.delete(where={"source": {"$exists": True}})
            except Exception as e2:
                print(f"Warning: Could not clear any documents: {e2}")
        
        jd_documents = []
        
        for filename in os.listdir(jd_dir):
            if filename.endswith('.txt') and not filename.endswith('_fresher.txt') and not filename.endswith('_senior.txt'):
                file_path = os.path.join(jd_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Create document with metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filename,
                        "type": "job_description",
                        "position": filename.replace('.txt', '').replace('_', ' ').title()
                    }
                )
                jd_documents.append(doc)
        
        if jd_documents:
            # Split documents
            splits = self.text_splitter.split_documents(jd_documents)
            # Add to vector store
            self.jd_vector_store.add_documents(splits)
            print(f"Loaded {len(jd_documents)} job descriptions into vector store")
    
    def process_resume(self, file_path: str, user_id: str) -> str:
        """Process uploaded resume and store in vector store"""
        if not self.azure_configured:
            # Fallback: just store the file path for later processing
            print("⚠️  Azure OpenAI not configured. Storing resume file for later processing.")
            return "Resume uploaded successfully (RAG processing disabled - Azure OpenAI not configured)"
            
        try:
            # Load PDF
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            # Split documents
            splits = self.text_splitter.split_documents(docs)
            
            # Add metadata
            for split in splits:
                split.metadata.update({
                    "user_id": user_id,
                    "type": "resume",
                    "source": file_path
                })
            
            # Clear existing resume for this user
            try:
                self.resume_vector_store._collection.delete(where={"user_id": user_id})
            except Exception as e:
                print(f"Warning: Could not clear existing resume for user {user_id}: {e}")
            
            # Add to vector store
            self.resume_vector_store.add_documents(splits)
            
            return "Resume processed successfully"
            
        except Exception as e:
            print(f"Error processing resume: {e}")
            return f"Error processing resume: {str(e)}"
    
    def get_resume_content(self, user_id: str) -> str:
        """Retrieve resume content for a user"""
        if not self.azure_configured:
            return ""
            
        try:
            retriever = self.resume_vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={'k': 10, 'lambda_mult': 0.25}
            )
            
            # Search for user's resume
            docs = retriever.get_relevant_documents("resume content")
            
            # Filter by user_id
            user_docs = [doc for doc in docs if doc.metadata.get("user_id") == user_id]
            
            if user_docs:
                return "\n\n".join(doc.page_content for doc in user_docs)
            else:
                return ""
                
        except Exception as e:
            print(f"Error retrieving resume: {e}")
            return ""
    
    def match_resume_with_jds(self, user_id: str, threshold: float = 0.65) -> List[Dict[str, Any]]:
        """Match user's resume with job descriptions using cosine similarity and AI analysis"""
        if not self.azure_configured:
            return [{
                "error": "Azure OpenAI not configured. Please set AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME environment variable."
            }]
            
        try:
            # Get resume content
            resume_content = self.get_resume_content(user_id)
            
            if not resume_content:
                return []
            
            print(f"📄 Resume content length: {len(resume_content)} characters")
            
            # Get all job descriptions from the jd folder
            jd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jd")
            jd_files = []
            
            for filename in os.listdir(jd_dir):
                if filename.endswith('.txt') and not filename.endswith('_fresher.txt') and not filename.endswith('_senior.txt'):
                    file_path = os.path.join(jd_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        jd_content = f.read()
                    jd_files.append((filename.replace('.txt', '').replace('_', ' ').title(), jd_content))
            
            print(f"📋 Found {len(jd_files)} job descriptions to analyze")
            
            # Generate embeddings for resume and all JDs
            texts = [resume_content] + [jd_text for _, jd_text in jd_files]
            vectors = self.embeddings.embed_documents(texts)
            
            resume_emb = vectors[0]
            jd_embs = [(name, vectors[i+1]) for i, (name, _) in enumerate(jd_files)]
            
            # Calculate cosine similarity
            def cosine_sim(a, b):
                import numpy as np
                a = np.array(a)
                b = np.array(b)
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            # Find best matches using cosine similarity
            matches = []
            for (jd_name, jd_text), (_, jd_emb) in zip(jd_files, jd_embs):
                similarity_score = cosine_sim(resume_emb, jd_emb)
                print(f"🔍 {jd_name}: Cosine similarity = {similarity_score:.3f}")
                
                # Only analyze JDs with decent similarity (above 0.3)
                if similarity_score > 0.3:
                    try:
                        print(f"🤖 AI analyzing: {jd_name}")
                        
                        # Create chain for detailed analysis
                        chain = self.matching_prompt | self.model
                        
                        # Get AI analysis
                        response = chain.invoke({
                            "resume_content": resume_content,
                            "jd_content": jd_text
                        })
                        
                        # Parse JSON response
                        try:
                            # Clean the response content - remove markdown code blocks if present
                            content = response.content.strip()
                            if content.startswith('```json'):
                                content = content[7:]  # Remove ```json
                            if content.startswith('```'):
                                content = content[3:]  # Remove ```
                            if content.endswith('```'):
                                content = content[:-3]  # Remove trailing ```
                            content = content.strip()
                            
                            result = json.loads(content)
                            ai_match_percentage = result.get("match_percentage", 0) / 100.0
                            
                            # Combine cosine similarity with AI analysis
                            # Weight: 40% cosine similarity, 60% AI analysis
                            combined_score = (similarity_score * 0.4) + (ai_match_percentage * 0.6)
                            
                            print(f"📊 {jd_name}: Cosine={similarity_score:.3f}, AI={ai_match_percentage:.3f}, Combined={combined_score:.3f}")
                            print(f"🎯 Threshold check: {combined_score:.3f} >= {threshold:.3f} = {combined_score >= threshold}")
                            
                            if combined_score >= threshold:
                                matches.append({
                                    "jd_title": jd_name,
                                    "jd_source": f"{jd_name.lower().replace(' ', '_')}.txt",
                                    "match_percentage": combined_score,
                                    "cosine_similarity": similarity_score,
                                    "ai_score": ai_match_percentage,
                                    "analysis": result.get("analysis", ""),
                                    "key_matches": result.get("key_matches", []),
                                    "missing_skills": result.get("missing_skills", []),
                                    "recommendations": result.get("recommendations", "")
                                })
                                print(f"✅ Match found: {jd_name} - {combined_score * 100:.1f}%")
                            else:
                                print(f"❌ Below threshold: {jd_name} - {combined_score * 100:.1f}%")
                        
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON parsing error for {jd_name}: {e}")
                            print(f"Raw response: {response.content}")
                            print(f"Cleaned content: {content}")
                            continue
                    
                    except Exception as e:
                        print(f"❌ Error analyzing {jd_name}: {e}")
                        continue
            
            # Sort by combined score (highest first)
            matches.sort(key=lambda x: x["match_percentage"], reverse=True)
            
            print(f"🎯 Found {len(matches)} matches above {threshold * 100}% threshold")
            return matches
            
        except Exception as e:
            print(f"❌ Error in resume-JD matching: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_jd_content(self, jd_filename: str) -> str:
        """Get content of a specific job description"""
        try:
            jd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jd")
            jd_path = os.path.join(jd_dir, jd_filename)
            
            if os.path.exists(jd_path):
                with open(jd_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
                
        except Exception as e:
            print(f"Error reading JD file: {e}")
            return ""

    def score_transcript(self, transcript: str) -> int:
        """Evaluate a transcript using Azure OpenAI and return a score (percentage out of 100)."""
        if not self.azure_configured or not self.model:
            return 0
        prompt = f"""
        You are an expert technical interviewer. Evaluate the following interview transcript and give a strict score out of 100 based on the quality, relevance, and completeness of the answers. Only return a number (integer, 0-100).
        
        TRANSCRIPT:
        {transcript}
        """
        try:
            response = self.model.invoke(prompt)
            # Extract integer score from response
            score = int(''.join(filter(str.isdigit, str(response.content))))
            return min(max(score, 0), 100)
        except Exception as e:
            print(f"Error scoring transcript: {e}")
            return 0

# Initialize the service
rag_service = RAGService() 