"use client";

import { useState } from "react";

interface Citation {
  document_name: string;
  text_snippet: string;
}

interface Message {
  role: "user" | "ai";
  content: string;
  citations?: Citation[];
  status?: string;
}

export default function RAGDashboard() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", content: "Welcome to the Enterprise Support Copilot. How can I help you today?" }
  ]);
  const [department, setDepartment] = useState("Engineering");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!query) return;
    
    const userMsg: Message = { role: "user", content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_query: query, metadata_filter: department })
      });
      const data = await response.json();
      
      const aiMsg: Message = { 
        role: "ai", 
        content: data.answer, 
        citations: data.citations,
        status: data.status 
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { role: "ai", content: "Error connecting to RAG backend. Ensure the FastAPI server is running." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex h-screen w-full bg-[#050a14] text-slate-200 overflow-hidden font-sans">
      {/* Sidebar: Metadata Filtering & Controls */}
      <aside className="w-80 glass-panel m-4 flex flex-col p-6 space-y-8">
        <div className="space-y-2">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            Enterprise RAG
          </h1>
          <p className="text-xs text-slate-500 uppercase tracking-widest">Production Ready v1.1</p>
        </div>

        <div className="space-y-4">
          <label className="text-sm font-medium text-slate-400">Department Filter</label>
          <select 
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option>Engineering</option>
            <option>Operations</option>
            <option>Human Resources</option>
          </select>
        </div>

        <div className="flex-grow"></div>
        
        <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
          <p className="text-xs text-blue-400 font-medium">Hybrid Engine: Active</p>
          <p className="text-[10px] text-blue-400/60 mt-1">Vector + RRF Fusion enabled</p>
        </div>
      </aside>

      {/* Main Chat Area */}
      <section className="flex-grow flex flex-col m-4 ml-0 space-y-4">
        <div className="flex-grow glass-panel overflow-y-auto p-6 space-y-6 scrollbar-hide">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl p-4 ${
                msg.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'chat-bubble-ai'
              }`}>
                <p className="text-sm leading-relaxed">{msg.content}</p>
                
                {msg.status === 'trusted' && (
                  <div className="mt-2 flex items-center text-[10px] text-emerald-400">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full mr-2 animate-pulse"></span>
                    Verified Source
                  </div>
                )}

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
                    <p className="text-[10px] font-bold text-slate-500 uppercase">Citations</p>
                    {msg.citations.map((c, ci) => (
                      <div key={ci} className="text-[11px] bg-white/5 p-2 rounded-lg border border-white/5 hover:border-blue-500 transition-colors">
                        <span className="text-blue-400 font-bold">[{c.document_name}]</span> {c.text_snippet.substring(0, 80)}...
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && <div className="text-xs text-blue-400 animate-pulse">Assistant is thinking...</div>}
        </div>

        {/* Input Bar */}
        <div className="h-20 glass-panel flex items-center px-6 space-x-4">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask a technical or policy question..."
            className="flex-grow bg-transparent outline-none text-sm placeholder:text-slate-600"
          />
          <button 
            onClick={handleSend}
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all shadow-lg shadow-blue-500/20"
          >
            Send
          </button>
        </div>
      </section>
    </main>
  );
}
