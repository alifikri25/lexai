const express = require('express');
const router = express.Router();
const axios = require('axios');
const { supabaseAdmin } = require('../services/supabase');
const authMiddleware = require('../middleware/auth');

// GET /api/chat/:documentId - Get chat history
router.get('/:documentId', authMiddleware, async (req, res) => {
    try {
        // Verify document belongs to user
        const { data: doc } = await supabaseAdmin
            .from('documents')
            .select('id')
            .eq('id', req.params.documentId)
            .eq('user_id', req.user.id)
            .single();

        if (!doc) {
            return res.status(404).json({ error: 'Dokumen tidak ditemukan' });
        }

        const { data, error } = await supabaseAdmin
            .from('chat_messages')
            .select('*')
            .eq('document_id', req.params.documentId)
            .eq('user_id', req.user.id)
            .order('created_at', { ascending: true });

        if (error) throw error;

        res.json({ messages: data || [] });
    } catch (err) {
        console.error('Get chat error:', err);
        res.status(500).json({ error: 'Gagal mengambil riwayat chat' });
    }
});

// POST /api/chat/:documentId - Send chat message
router.post('/:documentId', authMiddleware, async (req, res) => {
    try {
        const { message } = req.body;
        if (!message) {
            return res.status(400).json({ error: 'Pesan wajib diisi' });
        }

        // Verify document belongs to user
        const { data: doc } = await supabaseAdmin
            .from('documents')
            .select('id, title')
            .eq('id', req.params.documentId)
            .eq('user_id', req.user.id)
            .single();

        if (!doc) {
            return res.status(404).json({ error: 'Dokumen tidak ditemukan' });
        }

        // Save user message
        await supabaseAdmin
            .from('chat_messages')
            .insert({
                document_id: doc.id,
                user_id: req.user.id,
                role: 'user',
                content: message,
            });

        // Get recent chat history for context
        const { data: history } = await supabaseAdmin
            .from('chat_messages')
            .select('role, content')
            .eq('document_id', doc.id)
            .eq('user_id', req.user.id)
            .order('created_at', { ascending: false })
            .limit(10);

        const chatHistory = (history || []).reverse();

        // Send to AI service
        const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
        const aiResponse = await axios.post(`${aiServiceUrl}/api/chat`, {
            message,
            document_id: doc.id,
            chat_history: chatHistory,
        }, { timeout: 60000 });

        const assistantMessage = aiResponse.data.response;

        // Save assistant message
        const { data: savedMessage } = await supabaseAdmin
            .from('chat_messages')
            .insert({
                document_id: doc.id,
                user_id: req.user.id,
                role: 'assistant',
                content: assistantMessage,
            })
            .select()
            .single();

        res.json({
            message: savedMessage,
        });
    } catch (err) {
        console.error('Chat error:', err);
        res.status(500).json({ error: 'Gagal memproses pesan chat' });
    }
});

module.exports = router;
