const { createClient } = require('@supabase/supabase-js');

// Admin client (for server-side operations)
const supabaseAdmin = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Public client factory (for user-context operations)
function getSupabaseClient(accessToken) {
    return createClient(
        process.env.SUPABASE_URL,
        process.env.SUPABASE_ANON_KEY,
        {
            global: {
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
            },
        }
    );
}

module.exports = { supabaseAdmin, getSupabaseClient };
