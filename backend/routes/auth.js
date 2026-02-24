const express = require('express');
const router = express.Router();
const { supabaseAdmin } = require('../services/supabase');
const authMiddleware = require('../middleware/auth');

// POST /api/auth/register
router.post('/register', async (req, res) => {
    try {
        const { email, password, fullName } = req.body;

        if (!email || !password || !fullName) {
            return res.status(400).json({ error: 'Email, password, dan nama lengkap wajib diisi' });
        }

        const { data, error } = await supabaseAdmin.auth.admin.createUser({
            email,
            password,
            email_confirm: true,
            user_metadata: { full_name: fullName },
        });

        if (error) {
            return res.status(400).json({ error: error.message });
        }

        // Auto-login after register
        const { data: loginData, error: loginError } = await supabaseAdmin.auth.signInWithPassword({
            email,
            password,
        });

        if (loginError) {
            return res.status(400).json({ error: loginError.message });
        }

        res.status(201).json({
            message: 'Registrasi berhasil',
            user: data.user,
            session: loginData.session,
        });
    } catch (err) {
        console.error('Register error:', err);
        res.status(500).json({ error: 'Gagal mendaftarkan akun' });
    }
});

// POST /api/auth/login
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        if (!email || !password) {
            return res.status(400).json({ error: 'Email dan password wajib diisi' });
        }

        const { data, error } = await supabaseAdmin.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            return res.status(401).json({ error: 'Email atau password salah' });
        }

        res.json({
            message: 'Login berhasil',
            user: data.user,
            session: data.session,
        });
    } catch (err) {
        console.error('Login error:', err);
        res.status(500).json({ error: 'Gagal login' });
    }
});

// GET /api/auth/profile
router.get('/profile', authMiddleware, async (req, res) => {
    try {
        res.json({
            user: {
                id: req.user.id,
                email: req.user.email,
                fullName: req.user.user_metadata?.full_name || '',
                createdAt: req.user.created_at,
            },
        });
    } catch (err) {
        console.error('Profile error:', err);
        res.status(500).json({ error: 'Gagal mengambil profil' });
    }
});

// POST /api/auth/logout
router.post('/logout', authMiddleware, async (req, res) => {
    try {
        res.json({ message: 'Logout berhasil' });
    } catch (err) {
        res.status(500).json({ error: 'Gagal logout' });
    }
});

module.exports = router;
