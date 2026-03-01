const express = require('express');
const router = express.Router();
const axios = require('axios');
const { supabaseAdmin } = require('../services/supabase');
const authMiddleware = require('../middleware/auth');

const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';

// GET /api/legal-research/sessions — list all sessions
router.get('/sessions', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('legal_research_sessions')
            .select('id, title, created_at, updated_at')
            .eq('user_id', req.user.id)
            .order('updated_at', { ascending: false });

        if (error) throw error;
        res.json({ sessions: data || [] });
    } catch (err) {
        console.error('Get sessions error:', err.message);
        res.status(500).json({ error: 'Gagal mengambil daftar sesi' });
    }
});

// POST /api/legal-research/sessions — create new session
router.post('/sessions', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('legal_research_sessions')
            .insert({
                user_id: req.user.id,
                title: 'Riset Baru',
            })
            .select()
            .single();

        if (error) throw error;
        res.status(201).json({ session: data });
    } catch (err) {
        console.error('Create session error:', err.message);
        res.status(500).json({ error: 'Gagal membuat sesi baru' });
    }
});

// DELETE /api/legal-research/sessions/:id — delete a session
router.delete('/sessions/:id', authMiddleware, async (req, res) => {
    try {
        await supabaseAdmin
            .from('legal_research_sessions')
            .delete()
            .eq('id', req.params.id)
            .eq('user_id', req.user.id);

        res.json({ message: 'Sesi dihapus' });
    } catch (err) {
        console.error('Delete session error:', err.message);
        res.status(500).json({ error: 'Gagal menghapus sesi' });
    }
});

// GET /api/legal-research/sessions/:id/messages — get messages for a session
router.get('/sessions/:id/messages', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('legal_research_messages')
            .select('*')
            .eq('session_id', req.params.id)
            .eq('user_id', req.user.id)
            .order('created_at', { ascending: true });

        if (error) throw error;
        res.json({ messages: data || [] });
    } catch (err) {
        console.error('Get messages error:', err.message);
        res.status(500).json({ error: 'Gagal mengambil pesan' });
    }
});

// POST /api/legal-research — send a legal research question
router.post('/', authMiddleware, async (req, res) => {
    try {
        const { message, session_id } = req.body;
        if (!message) {
            return res.status(400).json({ error: 'Pertanyaan wajib diisi' });
        }

        let activeSessionId = session_id;

        // Create session if not provided
        if (!activeSessionId) {
            const { data: newSession, error: sessionError } = await supabaseAdmin
                .from('legal_research_sessions')
                .insert({
                    user_id: req.user.id,
                    title: message.substring(0, 60) + (message.length > 60 ? '...' : ''),
                })
                .select()
                .single();

            if (sessionError) throw sessionError;
            activeSessionId = newSession.id;
        }

        // Save user message
        await supabaseAdmin
            .from('legal_research_messages')
            .insert({
                user_id: req.user.id,
                session_id: activeSessionId,
                role: 'user',
                content: message,
                legal_refs: null,
            });

        // Get recent history for this session
        const { data: history } = await supabaseAdmin
            .from('legal_research_messages')
            .select('role, content')
            .eq('session_id', activeSessionId)
            .eq('user_id', req.user.id)
            .order('created_at', { ascending: false })
            .limit(10);

        const chatHistory = (history || []).reverse();

        // Send to AI service
        const aiResponse = await axios.post(`${aiServiceUrl}/api/legal-research`, {
            message,
            chat_history: chatHistory,
        }, { timeout: 120000 });

        const assistantResponse = aiResponse.data.response;
        const references = aiResponse.data.references || [];

        // Save assistant response
        const { data: savedMsg } = await supabaseAdmin
            .from('legal_research_messages')
            .insert({
                user_id: req.user.id,
                session_id: activeSessionId,
                role: 'assistant',
                content: assistantResponse,
                legal_refs: references,
            })
            .select()
            .single();

        // Update session title if first message
        if (!session_id) {
            await supabaseAdmin
                .from('legal_research_sessions')
                .update({ updated_at: new Date().toISOString() })
                .eq('id', activeSessionId);
        } else {
            await supabaseAdmin
                .from('legal_research_sessions')
                .update({ updated_at: new Date().toISOString() })
                .eq('id', activeSessionId);
        }

        res.json({
            message: savedMsg,
            references,
            session_id: activeSessionId,
        });
    } catch (err) {
        console.error('Legal research error:', err.message);
        res.status(500).json({ error: err.response?.data?.detail || 'Gagal memproses riset hukum' });
    }
});

module.exports = router;
