import asyncio
import os
import edge_tts

SCENES = [
    {
        "id": 1,
        "title": "Story",
        "target_duration": 30.0,
        "text": "Imagine Maria, who owns a small shop. On Monday, her best-selling product runs out, and customers leave empty-handed. On Friday, she opens the storage room and finds boxes of something she ordered too much of, and the money is stuck on the shelf. Maria is not bad at business. She is guessing. And every guess costs her money."
    },
    {
        "id": 2,
        "title": "The Idea",
        "target_duration": 30.0,
        "text": "We built an agent for people like Maria. It forecasts what will sell, decides what to reorder and what to discount, explains every decision in plain language, and waits for a human to approve before anything happens."
    },
    {
        "id": 3,
        "title": "How It Works",
        "target_duration": 45.0,
        "text": "There are four parts. First, a forecasting model predicts weekly demand per product. It is a statistical model, not a language model, so the numbers can be measured and defended. Second, simple rules turn the forecast into actions: reorder, discount, or do nothing. Third, Gemma, Google's open model, runs on AMD GPUs, explains each action, and drafts the supplier email. Fourth, Evolus runs the whole process, with a knowledge library for supplier rules, MCP to update the inventory system, and manager approval."
    },
    {
        "id": 4,
        "title": "The Forecast",
        "target_duration": 45.0,
        "text": "Here is how we measured the forecast. We tested the model on weeks it had never seen. Its error is 12.4 percent, against 13.5 percent for the best simple baseline, which is 7.8 percent better. This test used synthetic retail data, so read it as a demonstration of the method, not a final accuracy claim."
    },
    {
        "id": 5,
        "title": "The Actions",
        "target_duration": 45.0,
        "text": "These are example actions. This product is almost out of stock, so the system recommends reordering 420 units, marked urgent. This one has 18 weeks of cover, so it suggests a 20 percent discount. Every action shows the numbers behind it, so nothing is a black box."
    },
    {
        "id": 6,
        "title": "Gemma on AMD",
        "target_duration": 45.0,
        "text": "Now the agent. For each action, our app starts an Evolus workflow through its API. Gemma, served on AMD, reads the supplier rules from the knowledge library, explains the action, and writes the draft. In this example, one explanation takes about four seconds, and forty actions are processed in under two minutes."
    },
    {
        "id": 7,
        "title": "Human Approval",
        "target_duration": 30.0,
        "text": "Nothing runs without a person. The manager approves this order, and it is sent to the inventory system through MCP. They reject this discount because the margin is too low. The agent never acts alone."
    },
    {
        "id": 8,
        "title": "Value and Limits",
        "target_duration": 30.0,
        "text": "For Maria, that means fewer empty shelves and less money stuck in slow products. We are honest about the limits: our forecast test used synthetic data, and the next step is connecting to a real inventory system. Thank you for watching."
    }
]

async def generate_all_audio():
    out_dir = r"C:\Users\Besitzer\Downloads\inventory-agent-step1\inventory-agent\video_assets\audio"
    os.makedirs(out_dir, exist_ok=True)
    voice = "en-US-ChristopherNeural"
    # Rate slightly relaxed for calm, clear professional pacing
    rate = "-4%"
    
    for s in SCENES:
        filename = os.path.join(out_dir, f"scene_{s['id']}.mp3")
        print(f"Generating audio for Scene {s['id']}: {s['title']}...")
        tts = edge_tts.Communicate(s['text'], voice, rate=rate)
        await tts.save(filename)
        print(f"Saved: {filename}")

if __name__ == "__main__":
    asyncio.run(generate_all_audio())
