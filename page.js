"use client";
import { useState } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async () => {
    if (!input) return;
    const res = await fetch("https://YOUR_BACKEND_URL/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: input }),
    });
    const data = await res.json();
    setMessages([...messages, { user: input, bot: data.answer }]);
    setInput("");
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Medical RAG Chatbot</h1>
      <div className="h-96 overflow-y-scroll border p-2 mt-4">
        {messages.map((m, i) => (
          <div key={i}>
            <p><strong>You:</strong> {m.user}</p>
            <p><strong>Bot:</strong> {m.bot}</p>
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="border p-2 w-full mt-2"
        placeholder="Ask a medical question..."
      />
      <button
        onClick={sendMessage}
        className="bg-blue-500 text-white px-4 py-2 mt-2 rounded"
      >
        Send
      </button>
    </div>
  );
}
