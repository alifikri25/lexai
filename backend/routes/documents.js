const express = require('express');
const router = express.Router();
const multer = require('multer');
const axios = require('axios');
const { supabaseAdmin } = require('../services/supabase');
const authMiddleware = require('../middleware/auth');

// Multer setup for file upload (memory storage)
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 100 * 1024 * 1024 }, // 100MB max
    fileFilter: (req, file, cb) => {
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ];
        if (allowedTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Hanya file PDF dan DOCX yang diizinkan'));
        }
    },
});

// Multer error handler
const handleUpload = (req, res, next) => {
    upload.single('file')(req, res, (err) => {
        if (err instanceof multer.MulterError) {
            if (err.code === 'LIMIT_FILE_SIZE') {
                return res.status(413).json({ error: 'File terlalu besar. Maksimal 50MB.' });
            }
            return res.status(400).json({ error: err.message });
        } else if (err) {
            return res.status(400).json({ error: err.message });
        }
        next();
    });
};

// POST /api/documents/upload
router.post('/upload', authMiddleware, handleUpload, async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'File wajib diupload' });
        }

        const file = req.file;
        const userId = req.user.id;
        const fileExt = file.originalname.split('.').pop().toLowerCase();
        const fileName = `${userId}/${Date.now()}_${file.originalname}`;

        // Upload to Supabase Storage
        const { data: storageData, error: storageError } = await supabaseAdmin
            .storage
            .from('documents')
            .upload(fileName, file.buffer, {
                contentType: file.mimetype,
                upsert: false,
            });

        if (storageError) {
            console.error('Storage error:', storageError);
            return res.status(500).json({ error: 'Gagal mengupload file' });
        }

        // Save document metadata to DB
        const { data: docData, error: docError } = await supabaseAdmin
            .from('documents')
            .insert({
                user_id: userId,
                title: req.body.title || file.originalname.replace(`.${fileExt}`, ''),
                file_path: fileName,
                file_type: fileExt,
                file_size: file.size,
                status: 'pending',
            })
            .select()
            .single();

        if (docError) {
            console.error('DB error:', docError);
            return res.status(500).json({ error: 'Gagal menyimpan data dokumen' });
        }

        res.status(201).json({
            message: 'Dokumen berhasil diupload',
            document: docData,
        });
    } catch (err) {
        console.error('Upload error:', err);
        res.status(500).json({ error: err.message || 'Gagal mengupload dokumen' });
    }
});

// GET /api/documents
router.get('/', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('documents')
            .select('*, analyses(id, risk_score, created_at)')
            .eq('user_id', req.user.id)
            .order('created_at', { ascending: false });

        if (error) throw error;

        res.json({ documents: data });
    } catch (err) {
        console.error('Get documents error:', err);
        res.status(500).json({ error: 'Gagal mengambil daftar dokumen' });
    }
});

// GET /api/documents/:id
router.get('/:id', authMiddleware, async (req, res) => {
    try {
        const { data, error } = await supabaseAdmin
            .from('documents')
            .select('*, analyses(*)')
            .eq('id', req.params.id)
            .eq('user_id', req.user.id)
            .single();

        if (error || !data) {
            return res.status(404).json({ error: 'Dokumen tidak ditemukan' });
        }

        res.json({ document: data });
    } catch (err) {
        console.error('Get document error:', err);
        res.status(500).json({ error: 'Gagal mengambil dokumen' });
    }
});

// POST /api/documents/:id/analyze
router.post('/:id/analyze', authMiddleware, async (req, res) => {
    try {
        // Get document
        const { data: doc, error: docError } = await supabaseAdmin
            .from('documents')
            .select('*')
            .eq('id', req.params.id)
            .eq('user_id', req.user.id)
            .single();

        if (docError || !doc) {
            return res.status(404).json({ error: 'Dokumen tidak ditemukan' });
        }

        // Update status to analyzing
        await supabaseAdmin
            .from('documents')
            .update({ status: 'analyzing', updated_at: new Date().toISOString() })
            .eq('id', doc.id);

        // Download file from storage
        const { data: fileData, error: fileError } = await supabaseAdmin
            .storage
            .from('documents')
            .download(doc.file_path);

        if (fileError) {
            throw new Error('Gagal mengunduh file dari storage');
        }

        // Convert to buffer and send to AI service
        const buffer = Buffer.from(await fileData.arrayBuffer());
        const base64File = buffer.toString('base64');

        const aiServiceUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';

        // Step 1: Parse document
        const parseResponse = await axios.post(`${aiServiceUrl}/api/parse`, {
            file_base64: base64File,
            file_type: doc.file_type,
            file_name: doc.title,
        }, { timeout: 60000 });

        const documentText = parseResponse.data.text;

        // Step 2: Analyze document
        const analyzeResponse = await axios.post(`${aiServiceUrl}/api/analyze`, {
            text: documentText,
            document_id: doc.id,
        }, { timeout: 120000 });

        // Step 3: Create embeddings for RAG
        await axios.post(`${aiServiceUrl}/api/embed`, {
            text: documentText,
            document_id: doc.id,
        }, { timeout: 60000 });

        // Save analysis results
        const { data: analysisData, error: analysisError } = await supabaseAdmin
            .from('analyses')
            .insert({
                document_id: doc.id,
                summary: analyzeResponse.data.summary,
                clauses: analyzeResponse.data.clauses,
                risk_score: analyzeResponse.data.risk_score,
            })
            .select()
            .single();

        if (analysisError) throw analysisError;

        // Update document status
        await supabaseAdmin
            .from('documents')
            .update({ status: 'completed', updated_at: new Date().toISOString() })
            .eq('id', doc.id);

        res.json({
            message: 'Analisis selesai',
            analysis: analysisData,
        });
    } catch (err) {
        console.error('Analyze error:', err);

        // Update document status to error
        await supabaseAdmin
            .from('documents')
            .update({ status: 'error', updated_at: new Date().toISOString() })
            .eq('id', req.params.id);

        res.status(500).json({ error: err.message || 'Gagal menganalisis dokumen' });
    }
});

// DELETE /api/documents/:id
router.delete('/:id', authMiddleware, async (req, res) => {
    try {
        const { data: doc, error: docError } = await supabaseAdmin
            .from('documents')
            .select('*')
            .eq('id', req.params.id)
            .eq('user_id', req.user.id)
            .single();

        if (docError || !doc) {
            return res.status(404).json({ error: 'Dokumen tidak ditemukan' });
        }

        // Delete from storage
        await supabaseAdmin.storage.from('documents').remove([doc.file_path]);

        // Delete from DB (cascades to analyses, chat_messages, document_chunks)
        await supabaseAdmin.from('documents').delete().eq('id', doc.id);

        res.json({ message: 'Dokumen berhasil dihapus' });
    } catch (err) {
        console.error('Delete error:', err);
        res.status(500).json({ error: 'Gagal menghapus dokumen' });
    }
});

module.exports = router;
