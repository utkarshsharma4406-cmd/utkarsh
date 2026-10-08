import os
import sys

from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, RunContext, WorkerOptions, cli, function_tool
from livekit.plugins import openai, silero


class DentalReceptionist(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly, patient voice receptionist for a dental clinic. "
                "Speak naturally and keep answers short. Help callers with general "
                "dental-office questions, collect their name and phone number, and "
                "take appointment requests. Never invent clinic-specific facts such "
                "as hours, prices, insurance coverage, address, or availability; say "
                "you do not have that information and offer to pass along a question. "
                "Do not diagnose or recommend treatment. For severe or urgent "
                "symptoms, advise the caller to contact a qualified dental or medical "
                "professional, and direct an immediate emergency to local emergency "
                "services. Before collecting details, explain that this microphone "
                "demo does not save them or contact the clinic. Ask the caller to "
                "spell or repeat unclear details. An appointment request is not a "
                "confirmed booking: collect a preferred date and time, then make "
                "that limitation clear."
            )
        )
        self.name: str | None = None
        self.phone_number: str | None = None

    @function_tool()
    async def save_contact(
        self,
        context: RunContext,
        name: str,
        phone_number: str,
    ) -> str:
        """Keep the caller's name and phone number in memory for this demo session."""
        cleaned_name = name.strip()
        cleaned_phone = phone_number.strip()
        digit_count = sum(character.isdigit() for character in cleaned_phone)

        if not cleaned_name:
            return "I didn't catch the caller's name. Please ask for it again."
        if not 7 <= digit_count <= 15:
            return "That phone number doesn't look complete. Please ask the caller to repeat it."

        self.name = cleaned_name
        self.phone_number = cleaned_phone
        return (
            "Contact details are noted in memory for this demo session only. "
            "Please read the name and phone number back and ask the caller to confirm."
        )

    @function_tool()
    async def request_appointment(
        self,
        context: RunContext,
        preferred_date: str,
        preferred_time: str,
        reason: str = "Not provided",
    ) -> str:
        """Record a preferred appointment time as an unconfirmed demo request."""
        if not self.name or not self.phone_number:
            return "No contact details have been captured yet. Please collect and confirm the caller's name and phone number first."
        if not preferred_date.strip() or not preferred_time.strip():
            return "A preferred date and time are both needed. Please ask the caller for whichever detail is missing."

        return (
            f"Demo request noted for {self.name} ({self.phone_number}): "
            f"{preferred_date.strip()} at {preferred_time.strip()}. "
            f"Reason: {reason.strip() or 'Not provided'}. "
            "This was not sent to the clinic and is not a confirmed appointment."
        )


async def entrypoint(ctx: JobContext) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add your key to the local .env file; "
            "see the README for setup instructions."
        )

    session = AgentSession(
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="alloy"),
        vad=silero.VAD.load(),
    )
    await session.start(room=ctx.room, agent=DentalReceptionist())
    await session.generate_reply(
        instructions=(
            "Greet the caller warmly. Briefly explain that this is a microphone "
            "prototype: information is not saved or sent to the clinic, and "
            "appointment requests are not confirmed. Ask how you can help."
        )
    )


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "demo":
        from local_demo import main as run_local_demo

        run_local_demo()
    else:
        load_dotenv()
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
