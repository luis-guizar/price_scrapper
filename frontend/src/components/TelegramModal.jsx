import React, { useState } from 'react'
import { Send, X } from 'lucide-react'
import axios from 'axios'

export default function TelegramModal({ isOpen, onClose }) {
    const [message, setMessage] = useState('')
    const [sending, setSending] = useState(false)
    const [error, setError] = useState(null)

    if (!isOpen) return null

    const handleSend = async () => {
        if (!message.trim()) return

        setSending(true)
        setError(null)
        try {
            await axios.post('/api/notifications/telegram', { message })
            setMessage('')
            onClose()
            alert('Message sent successfully!')
        } catch (err) {
            setError('Failed to send message: ' + (err.response?.data?.detail || err.message))
        } finally {
            setSending(false)
        }
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-[2px] p-4">
            <div className="bg-[#0d1524] border border-slate-600/40 rounded-2xl w-full max-w-lg shadow-2xl shadow-black/60 overflow-hidden" style={{ animation: 'modalSlideIn 0.2s ease-out' }}>
                <div className="px-6 py-4 border-b border-slate-700/40 flex justify-between items-center bg-[#080f1a]/60">
                    <h3 className="font-semibold text-slate-100 flex items-center gap-2 tracking-tight">
                        <Send size={18} className="text-blue-400" />
                        Broadcast Update
                    </h3>
                    <button onClick={onClose} className="text-slate-500 hover:text-slate-200 hover:bg-slate-800/70 p-1.5 rounded-lg transition-colors duration-150">
                        <X size={18} />
                    </button>
                </div>

                <div className="p-6">
                    <p className="text-slate-500 text-sm mb-4">
                        Send a manual notification to the Telegram channel. Adding an emoji helps it stand out!
                    </p>

                    <textarea
                        className="input-base w-full h-32 rounded-xl p-4 resize-none mb-4"
                        placeholder="Type your message here..."
                        value={message}
                        onChange={e => setMessage(e.target.value)}
                        autoFocus
                    />

                    {error && (
                        <div className="bg-red-500/10 text-red-500 text-sm p-3 rounded-lg mb-4 border border-red-500/20">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/70 transition-colors duration-150"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={sending || !message.trim()}
                            className="px-5 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-500 active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 transition-all duration-150 shadow-sm"
                        >
                            {sending ? 'Sending...' : 'Send Broadcast'}
                            {!sending && <Send size={16} />}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
