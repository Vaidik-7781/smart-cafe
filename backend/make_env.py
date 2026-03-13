content = """SUPABASE_URL=https://efgaigfrisamqzdwhdfe.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmZ2FpZ2ZyaXNhbXF6ZHdoZGZlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzQyMDc4NSwiZXhwIjoyMDg4OTk2Nzg1fQ.EWJtTrk-0Z47s9MDSva4zfE0TkqO3Y1LqZccHN9p7Yo
ADMIN_TOKEN=cafe-admin-9X3kP2Lm74SecureToken
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=guptavaidik2610@gmail.com
SMTP_PASS=cvpkstpxhejpjade
FROM_EMAIL=noreply@smartcafe.in
FROM_NAME=Smart Cafe
CLOUDINARY_CLOUD_NAME=dufeizdnb
CLOUDINARY_API_KEY=334566259841327
CLOUDINARY_API_SECRET=ri8H1m90Q6m5dTXSE71P6WJKVfo
CLOUDINARY_UPLOAD_PRESET=cafe_menu_images
ENVIRONMENT=development
FRONTEND_URL=http://127.0.0.1:5500
TAX_RATE=0.09
JWT_SECRET=SmartCafeJWTSecret9xP31Lm4SecureRandom
"""

with open(".env", "w") as f:
    f.write(content)

print("SUCCESS - .env created!")