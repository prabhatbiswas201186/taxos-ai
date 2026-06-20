@echo off
echo Deploying TAXOS AI...
git add -A
git commit -m "chore: deploy"
git push origin main
echo Pushed. Check Vercel dashboard for deployment.
