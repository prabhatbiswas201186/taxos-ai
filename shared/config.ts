export const DATABASE_URL = process.env.DATABASE_URL || "";
export const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
export const SUPABASE_URL = process.env.SUPABASE_URL || "";
export const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || "";
export const JWT_SECRET = process.env.JWT_SECRET || "taxos-ai-secret-change-in-production";
export const RESEND_API_KEY = process.env.RESEND_API_KEY || "";

export const APP_CONFIG = {
  name: "TAXOS AI",
  version: "1.0.0",
  supportEmail: "support@taxos.ai",
  uploadMaxSize: 10 * 1024 * 1024, // 10MB per file
  allowedFileTypes: [".pdf", ".jpg", ".jpeg", ".png", ".xlsx", ".csv", ".docx"],
};
