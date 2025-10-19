# config.py
import os
import sys

class Config:
    """Configuration class with multiple fallback methods"""
    
    @staticmethod
    def get_bot_token():
        """Get bot token with multiple fallback approaches"""
        
        # Method 1: Environment variable (Railway's standard approach)
        token = os.getenv('BOT_TOKEN')
        if token:
            print("✅ Loaded BOT_TOKEN from environment variable")
            return token
        
        # Method 2: Railway's service token file (alternative Railway method)
        service_token_path = '/etc/railway/tokens/BOT_TOKEN'
        if os.path.exists(service_token_path):
            try:
                with open(service_token_path, 'r') as f:
                    token = f.read().strip()
                    if token:
                        print("✅ Loaded BOT_TOKEN from Railway service token file")
                        return token
            except Exception as e:
                print(f"⚠️  Failed to read Railway token file: {e}")
        
        # Method 3: Check for token in current directory
        token_files = ['bot_token.txt', 'token.txt', '.token', 'config/token.txt']
        for token_file in token_files:
            if os.path.exists(token_file):
                try:
                    with open(token_file, 'r') as f:
                        token = f.read().strip()
                        if token:
                            print(f"✅ Loaded BOT_TOKEN from file: {token_file}")
                            return token
                except Exception as e:
                    print(f"⚠️  Failed to read {token_file}: {e}")
        
        # Method 4: For Railway - create a token file during build
        railway_token = Config._get_railway_token()
        if railway_token:
            return railway_token
        
        # Final fallback: hardcoded for testing (REMOVE THIS IN PRODUCTION)
        # This is just to get it running - we'll replace this later
        test_token = "7747855846:AAFWjqqZXNBpwFFjrAQi3fjT5qwBbjcJCNs"  # Your actual token
        print("🚨 USING HARDCODED TOKEN FOR TESTING - REPLACE WITH PROPER CONFIG")
        return test_token
    
    @staticmethod
    def _get_railway_token():
        """Try Railway-specific methods"""
        # Check if we're running on Railway
        if os.getenv('RAILWAY_PROJECT_ID'):
            print("🔍 Running on Railway - checking alternative token methods...")
            
            # Method: Check build-time environment
            build_token = os.getenv('RAILWAY_BOT_TOKEN') or os.getenv('BUILD_BOT_TOKEN')
            if build_token:
                return build_token
            
            # Method: Create token file from build args
            build_args_token = Config._get_from_build_args()
            if build_args_token:
                return build_args_token
        
        return None
    
    @staticmethod
    def _get_from_build_args():
        """Extract token from build arguments or other Railway-specific locations"""
        # Check for token in common Railway paths
        paths_to_check = [
            '/app/bot_token',
            '/tmp/bot_token', 
            '/etc/railway/token',
            '/run/secrets/bot_token'
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        token = f.read().strip()
                        if token and len(token) > 10:
                            print(f"✅ Found token in {path}")
                            return token
                except:
                    continue
        
        return None

# Global config instance
BOT_TOKEN = Config.get_bot_token()
ANNOUNCEMENT_CHANNEL = os.getenv('ANNOUNCEMENT_CHANNEL', '')