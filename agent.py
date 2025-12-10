from datetime import datetime
import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib import response
from fastapi import FastAPI, APIRouter

from pymongo import AsyncMongoClient
from requests import session
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    RoomInputOptions,
    function_tool,
    RunContext
)
from livekit.plugins import (
    cartesia,
    groq,
    deepgram,
    noise_cancellation,
    silero,
    elevenlabs,
    openai,
    google,

)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://shreyas:shreyas@shreyas.8rxrw.mongodb.net/?retryWrites=true&w=majority&appName=shreyas")
DB_NAME      = os.getenv("DB_NAME", "Calls")
COLLECTION   = os.getenv("COLLECTION", "Total_calls")


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


router = APIRouter()


CURRENT_CTX = None

class Assistant(Agent):
    
    
    def __init__(self) -> None:
        # This project is configured to use Deepgram STT, OpenAI LLM and Cartesia TTS plugins
        # Other great providers exist like Cerebras, ElevenLabs, Groq, Play.ht, Rime, and more
        # Learn more and pick the best one for your app:
        # https://docs.livekit.io/agents/plugins
        super().__init__(
            instructions="""1) Identity
You are Ravi, a virtual sales representative at VisionIT.  
VisionIT sells refurbished laptops, desktops, monitors, and computer peripherals such as keyboards, mice, SSDs, and RAMs.  
You handle inbound and outbound calls to understand customer needs and provide the best refurbished computer solutions.
2) Call Flow Logic  

1. Check Availability  
- If the customer says no, **call later**, or **tries to skip the call**:  
  > "Okay, no problem. I will call you some other time. Have a nice day!"  
  *(End the call politely.)*

- If the customer agrees to talk:  
  > "Thank you. I will keep it short."

2. Company Introduction  
> "I am calling from VisionIT. We sell refurbished laptops, desktops, monitors, and computer accessories.  
We help businesses, schools, and professionals get high-quality computers at low prices.  
All our products come with warranty and service support."

3. Need Discovery  
> "Can you please tell me what kind of computers you are using right now?"  
> "Do you face any problems with your current systems like slow speed or hardware issues?"  
> "Are you planning to buy new computers or upgrade your existing setup?"

Listen carefully to what the customer says and understand their needs before replying.

4. Solution and Value Pitch  
When the customer explains their situation, reply politely and offer a matching solution.

- **If they have budget concerns:**  
  > "We offer refurbished systems that work like new but cost almost half the price."

- **If they have performance issues:**  
  > "We can provide systems upgraded with SSDs and extra RAM for better speed and reliability."

- **If they are buying for business or institution:**  
  > "We can supply bulk laptops or desktops with warranty and doorstep delivery anywhere in India."

After sharing the solution, say:  
> "Would you like me to send you a quotation or product list that fits your needs?"
3) Style Guidelines  
- Use simple, polite, and professional language.  
- Always listen first, then give your response.  
- Speak in a clear and helpful tone.  
- Keep the conversation short and natural.  
- Collect customer details step-by-step:  
  - Name  
  - Company or type of work  
  - Contact email or WhatsApp number  
  - Quantity or budget (if known)

# Example Conversation Flow

**Ravi:**  
"Hello! This is Ravi from VisionIT. Is this a good time to talk for two minutes?"

**Customer:**  
"Yes, please continue."

**Ravi:**  
"Thank you. I am calling from VisionIT. We provide refurbished laptops, desktops, and accessories.  
We help people and businesses reduce computer costs while keeping high performance.  
Can you please tell me what kind of systems you are using now?"

**Customer:**  
"We have old desktops that are getting slow."

**Ravi:**  
"I understand. That happens often with older systems.  
We can offer refurbished desktops with SSDs and warranty at almost half the price of new ones.  
Would you like me to send you a quotation or product list?"

Response Guidelines  
- Always stay in your sales agent role.  
- Keep your tone polite, confident, and respectful.  
- Focus on helping the customer, not just selling.  
- If the customer is not interested, end the call nicely.  
- Always thank the customer before ending the call.

follwing are the function tools as follows :
1)get_current_date_and_time:Get the current date and time.
2)send_email:If the user ask to send email then request the user to spell the each letter then make its string of letters and confirm before sending by spelling letter by letter the email.If email is not correct then start over again to get the correct email address.
""",
            stt=deepgram.STT(),
            llm=groq.LLM(model="llama-3.3-70b-versatile"),
            #llm=google.LLM(model="gemini-2.0-flash"),
           # llm=openai.LLM.with_deepseek(model="deepseek-chat"),
            tts=cartesia.TTS(api_key=os.getenv("CARTESIA_API_KEY"),voice="fd2ada67-c2d9-4afe-b474-6386b87d8fc3"),
            # use LiveKit's transformer-based turn detector
            turn_detection=MultilingualModel(),
            
        )
#     @function_tool
#     async def get_current_date_and_time(self,context: RunContext) -> str:
#         """Get the current date and time."""
#        # current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
#         current_datetime="sunday afterrnon 12pm"
#         return "The current date and time is sunday afternoon 12 pm"

#     @function_tool()
#     async def send_email(self, context: RunContext, to_email: str) -> str:
#         """
#         If the user ask to send email then request the user to spell the each letter then make its string of letters and confirm before sending by spelling letter by letter the email.If email is not correct then start over again to get the correct email address.
#         """

#         # Static subject & body (predefined by you)

#         subject = "Thank you for your interest in VisionIT"
#         body = (
#             "Hello,\n\n"
#             "Thank you for speaking with us today. As discussed, here is a summary of our offerings:\n"
#             "- Refurbished laptops, desktops, monitors, accessories with warranty\n"
#             "- Custom upgrade options (SSD, RAM, etc.)\n"
#             "- Bulk supplies for businesses, schools, institutions\n\n"
#             "If you need a formal quotation or product list, just reply to this email or reach out to us.\n\n"
#             "Regards,\n"
#             "VisionIT Team"
#         )

#         smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
#         smtp_port = int(os.getenv("SMTP_PORT", 587))
#         smtp_user = os.getenv("SMTP_USER")
#         smtp_pass = os.getenv("SMTP_PASS")

#         if not smtp_user or not smtp_pass:
#             return "Error: SMTP credentials not configured."

#         msg = MIMEMultipart("alternative")
#         msg["From"] = smtp_user
#         msg["To"] = to_email
#         msg["Subject"] = subject
#         msg.attach(MIMEText(body, "plain"))

#         try:
#             server = smtplib.SMTP(smtp_host, smtp_port)
#             server.starttls()
#             server.login(smtp_user, smtp_pass)
#             server.sendmail(smtp_user, to_email, msg.as_string())
#             server.quit()
#             s=f"✅ Email sent to {to_email}."
#             return s
#         except Exception as e:
#             error=f"❗ Failed to send email: {str(e)}"
#             return error

#     @function_tool()
#     async def store_leads(self, context: RunContext) -> str:
#         """
#         aa
#         """
#         API_KEY = os.getenv("HUBSPOT_API_KEY")
#         client = HubSpot(api_key=API_KEY)

#         contact_input = SimplePublicObjectInputForCreate(
#         properties={
#         "firstname": "FirstName",
#         "lastname": "LastName",
#         "phone": "+1234567890",
#         "company": "My Company Pvt Ltd",
#         "address": "123 Example Street",   # HubSpot default property “address”
#         "city": "Example City",
#         "state": "Example State",
#         # For lead status — use internal property name, e.g.:
#         "hs_lead_status": "New",            # Or any valid status value your portal uses
#     }
# )

#         created = client.crm.contacts.basic_api.create(SimplePublicObjectInputForCreate=contact_input)
#         print("Contact created:", created.id)
#         if created.id:
#             return "Lead submitted successsfully !"
#         else:
#             return "Failed to store lead information."

    async def on_enter(self):
        #The agent should be polite and greet the user when it joins :)
        # self.session.generate_reply(
        #     instructions="Hey, how can I help you today?", allow_interruptions=True
        # )
        pass

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    global CURRENT_CTX
    CURRENT_CTX = ctx
    logger.info("connecting to room %s", ctx.room.name)
    
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Parse metadata to check if this is an outbound call
    phone_number = None
    if ctx.job.metadata:
        try:
            dial_info = json.loads(ctx.job.metadata)
            phone_number = dial_info.get("phone_number")
        except (json.JSONDecodeError, KeyError):
            logger.warning("Could not parse metadata: %s", ctx.job.metadata)

    # If a phone number was provided, place an outbound call
    # This allows the same agent to handle inbound/outbound calls and web/mobile
    sip_participant_identity = phone_number if phone_number else None
    
    if phone_number:
        trunk_id = os.getenv("LIVEKIT_TRUNK_ID")
        if not trunk_id:
            logger.error("LIVEKIT_TRUNK_ID not set in environment variables")
            ctx.shutdown()
            return

        logger.info("Placing outbound call to %s", phone_number)
        try:
            # Create SIP participant to place the outbound call
            # This will dial the phone number and wait for answer
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    # This ensures the participant joins the correct room
                    room_name=ctx.room.name,
                    # This is the outbound trunk ID to use
                    sip_trunk_id=trunk_id,
                    # The outbound phone number to dial
                    sip_call_to=phone_number,
                    participant_identity=sip_participant_identity,
                    # This will wait until the call is answered before returning
                    wait_until_answered=True,
                )
            )
            logger.info("Call picked up successfully")     #called picked suucwess fully message 
        except api.TwirpError as e:
            logger.error(
                "Error creating SIP participant: %s, SIP status: %s %s",    #failed to create a call due to busy or sip trunk issue 
                e.message,
                e.metadata.get('sip_status_code'),
                e.metadata.get('sip_status'),
            )
            ctx.shutdown()
            return

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info("starting voice assistant for participant %s", participant.identity)

    # usage_collector = metrics.UsageCollector()

    # Log metrics and collect usage data
    # def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
    #     metrics.log_metrics(agent_metrics)
    #     usage_collector.collect(agent_metrics)

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # minimum delay for endpointing, used when turn detector believes the user is done with their turn
        min_endpointing_delay=0.4,
        # maximum delay for endpointing, used when turn detector does not believe the user is done with their turn
        max_endpointing_delay=1.5,
        preemptive_generation=True
    )

    # Trigger the on_metrics_collected function when metrics are collected
    # session.on("metrics_collected", on_metrics_collected)
 
    # await session.start(  
    #     room=ctx.room,
    #     agent=Assistant(),
    #     room_options=RoomInputOptions(
    #         # enable background voice & noise cancellation, powered by Krisp
    #         # included at no additional cost with LiveKit Cloud
    #         noise_cancellation=noise_cancellation.BVC(),
    #     ),
    # )
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
   

    async def save_complete_transcript():
        try:
            # save the history to json file
            mongo_client = AsyncMongoClient(MONGODB_URI)
            db = mongo_client[DB_NAME]
            collection = db[COLLECTION]
            history = session.history.to_dict()["items"]
            doc={
                "phone_number": phone_number,
                "timestamp": datetime.now(),
                "transcript": history
            }
            insert_result = await collection.insert_one(doc) 
             # Async insert
            print("✅ Transcript saved to MongoDB with ID:", str(insert_result.inserted_id))
            # with open(
            #     f"history/transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            #     "w"
            # ) as f:
            #     json.dump(history, f, indent=4)
        except Exception as e:
            print(f"An error occurred while saving transcript: {e}")
            response = str(e)
            print(response)

    ctx.add_shutdown_callback(save_complete_transcript)


   
    # Only greet the user for inbound calls
    # For outbound calls, it's more customary for the recipient to speak first
    # The agent will automatically respond after the user's turn has ended
    #if phone_number is None:
    await session.generate_reply(
            instructions="Say: Hello! This is Ravi from VisionIT. Is this a good time to talk for two minutes?",
            allow_interruptions=False,
        )
    
@router.post("/stop")
def stop_worker():
    global CURRENT_CTX

    if CURRENT_CTX is None:
        return {"error": "Worker not running / no active context"}

    try:
        CURRENT_CTX.shutdown()
        return {"status": "Worker shutdown triggered"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-agent",
            prewarm_fnc=prewarm,
        ),
    )
