"""
Simple CLI tool to make outbound calls
Usage: python call_handler.py +1234567890
"""
import asyncio
import logging
import sys
from dispatcher import OutboundCallDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("call-handler")


async def make_single_call(phone_number: str, caller_id: str = "VisionIT Sales"):
    """Make a single outbound call"""
    dispatcher = OutboundCallDispatcher()
    result = await dispatcher.make_call(phone_number, caller_id=caller_id)
    
    if result["success"]:
        print("✅ Call initiated successfully!")
        print(f"   Room: {result['room_name']}")
        print(f"   Phone: {result['phone_number']}")
    else:
        print(f"❌ Call failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)



async def make_bulk_calls(phone_numbers: list[str], caller_id: str = "VisionIT Sales"):
    """Make multiple outbound calls"""
    dispatcher = OutboundCallDispatcher()
    results = await dispatcher.make_bulk_calls(phone_numbers, caller_id=caller_id)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print("\n📊 Call Summary:")
    print(f"   Total: {len(results)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    
    if failed > 0:
        print("\n❌ Failed calls:")
        for r in results:
            if not r["success"]:
                print(f"   - {r['phone_number']}: {r.get('error', 'Unknown error')}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single call:  python call_handler.py +1234567890")
        print("  Bulk calls:   python call_handler.py +1234567890 +0987654321 +1122334455")
        print("\nNote: Phone numbers must be in E.164 format (e.g., +1234567890)")
        sys.exit(1)
    
    phone_numbers = sys.argv[1:]
    
    if len(phone_numbers) == 1:
        asyncio.run(make_single_call(phone_numbers[0]))
    else:
        asyncio.run(make_bulk_calls(phone_numbers))


if __name__ == "__main__":
    main()

