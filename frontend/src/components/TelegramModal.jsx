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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
                <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
                    <h3 className="font-semibold text-white flex items-center gap-2">
                        <Send size={18} className="text-blue-500" />
                        Broadcast Update
                    </h3>
                    <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6">
                    <p className="text-slate-400 text-sm mb-4">
                        Send a manual notification to the Telegram channel. Adding an emoji helps it stand out!
                    </p>

                    <textarea
                        className="w-full h-32 bg-slate-800 border-none rounded-xl p-4 text-white focus:ring-2 focus:ring-blue-500 resize-none placeholder:text-slate-600 mb-4"
                        placeholder="Type your message here..."
                        value={message}
                        onChange={e => setMessage(e.target.value)}
                        autoFocus
                    />

                    {error && (
                        <div className="bg-red-500/10 text-red-500 text-sm p-3 rounded-lg mb-4">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={sending || !message.trim()}
                            className="px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
