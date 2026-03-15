import React, { useMemo, useState } from 'react';
import { coachAPI, parseApiError } from '../services/api';
import styles from './AICoach.module.css';

export const AICoachPage = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'I am your AI Interview Coach. Ask me what to improve next.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const history = useMemo(() => messages.slice(-12), [messages]);

  const sendMessage = async () => {
    const content = input.trim();
    if (!content || loading) return;

    const nextMessages = [...messages, { role: 'user', content }];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const response = await coachAPI.chat({ message: content, history });
      const reply = response?.data?.reply || 'No response generated.';
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch (err) {
      setError(parseApiError(err, 'AI Coach is unavailable.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1>AI Coach</h1>
        <p>Context-aware coaching from your resume, scores, and interview history.</p>
      </header>

      <div className={styles.chatWrap}>
        <div className={styles.messages}>
          {messages.map((item, index) => (
            <div key={`${item.role}-${index}`} className={`${styles.bubble} ${item.role === 'user' ? styles.user : styles.assistant}`}>
              {item.content}
            </div>
          ))}
        </div>

        {error ? <p className={styles.error}>{error}</p> : null}

        <div className={styles.composer}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask: How do I improve system design for backend interviews?"
            rows={3}
          />
          <button type="button" onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? 'Thinking...' : 'Send'}
          </button>
        </div>
      </div>
    </section>
  );
};

export default AICoachPage;
