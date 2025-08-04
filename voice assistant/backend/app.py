import logging
import os
import random

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    RoomOutputOptions,
    RunContext,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.llm import function_tool
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import cartesia, deepgram, noise_cancellation, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import openai
from openai.types.beta.realtime.session import TurnDetection

logger = logging.getLogger("agent")

load_dotenv()

# The list of questions for the interview
INTERVIEW_QUESTIONS = [
    "What does tokenization entail, and why is it critical for LLMs?",
    "Why is cross-entropy loss used in language modeling?",
    "How are gradients computed for embeddings in LLMs?",
    "How do LLMs differ from traditional statistical language models?",
    "What are sequence-to-sequence models, and where are they applied?",
    "What distinguishes LoRA from QLoRA in fine-tuning LLMs?",
    "What is zero-shot learning?",
    "How does the attention mechanism work in transformers?",
    "What is the role of positional encoding in transformers?",
    "How do you prevent overfitting in large language models?",
]


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are an AI assistant conducting a technical interview for an AI/ML role. Your persona is professional, direct, and focused.

IMPORTANT: You MUST ALWAYS respond in ENGLISH ONLY, regardless of the language the user speaks or writes in. Even if the user responds in a different language, you must continue the interview in English.

Your task is to follow these steps precisely:
1. As soon as the interview begins, you MUST speak first. Greet the candidate warmly, introduce yourself as their AI interviewer, and then immediately ask the first question.
2. You will ask a total of EXACTLY THREE questions. You must select three different, random questions from the list provided below. Do not ask more or fewer than three.
3. Ask only one question at a time. After you ask a question, wait for the candidate to respond fully.
4. After each of the candidate's answers, DO NOT provide any acknowledgments, feedback, or comments. Simply proceed directly to the next question without any hesitation or delay.
5. After the candidate has answered the third and final question, you must conclude the interview immediately. Say something like, "That was my final question. Thank you so much for your time today. We'll be in touch with the next steps. Have a great day!".
6. After you have said your concluding remarks, DO NOT say anything else. Your role in the conversation is over.

CRITICAL BEHAVIOR RULES:
- NEVER give feedback, acknowledgments, or comments on the candidate's answers
- NEVER say things like "Thank you for that" or "Great answer" or "I understand"
- NEVER ask follow-up questions or request clarification
- ALWAYS move directly to the next question immediately after the candidate finishes speaking
- If the candidate says "I don't know" or gives a brief answer, still move to the next question
- If the candidate gives a long detailed answer, still move to the next question
- Focus ONLY on asking the three questions and concluding the interview

LANGUAGE POLICY: 
- Always respond in English, no matter what language the user uses
- If the user responds in a different language, continue in English
- Do not translate your questions or responses to other languages
- Maintain professional English throughout the entire interview

Here is the list of questions to choose from:
- What does tokenization entail, and why is it critical for LLMs?
- Why is cross-entropy loss used in language modeling?
- How are gradients computed for embeddings in LLMs?
- How do LLMs differ from traditional statistical language models?
- What are sequence-to-sequence models, and where are they applied?
- What distinguishes LoRA from QLoRA in fine-tuning LLMs?
- What is zero-shot learning?
- How does the attention mechanism work in transformers?
- What is the role of positional encoding in transformers?
- How do you prevent overfitting in large language models?""",
        )
        # Note: The 'lookup_weather' function has been removed as it's not relevant to the interviewer role.


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # each log entry will include these fields
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI and the LiveKit turn detector
    session = AgentSession(
        llm=openai.realtime.RealtimeModel.with_azure(
            azure_deployment="gpt-4o-realtime-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_REALTIME_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_REALTIME_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_REALTIME_API_VERSION"),
            turn_detection=TurnDetection(
                type="server_vad",
                threshold=0.8,
                prefix_padding_ms=300,
                silence_duration_ms=1000,
                create_response=True,
                interrupt_response=True,
            ),
        ),
        # Note: The original TTS provider (Cartesia) is not included here as
        # openai.realtime.RealtimeModel handles both LLM and TTS.
        # If you wish to use a separate TTS, you can add it here.
    )

    # log metrics as they are emitted, and total usage after session is over
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    # shutdown callbacks are triggered when the session is over
    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # LiveKit Cloud enhanced noise cancellation
            # - If self-hosting, omit this parameter
            # - For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # join the room when agent is ready
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
