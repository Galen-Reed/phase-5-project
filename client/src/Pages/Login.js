import React, { useState, useEffect } from 'react';
import {
  CssVarsProvider,
  useColorScheme,
  extendTheme
} from '@mui/joy/styles';
import {
  Sheet,
  Typography,
  FormControl,
  FormLabel,
  Input,
  Button,
  Link,
  Divider,
  Alert,
  IconButton,
  Select,
  Option,
  Box,
  Stack
} from '@mui/joy';
import { Coffee, Github, Eye, EyeOff, Moon, Sun, Laptop } from 'lucide-react';

// Custom theme with coffee-inspired colors
const theme = extendTheme({
  colorSchemes: {
    light: {
      palette: {
        primary: {
          50: '#fdf2f8',
          100: '#fce7f3',
          200: '#fbcfe8',
          300: '#f9a8d4',
          400: '#f472b6',
          500: '#8B4513', // Coffee brown
          600: '#A0522D',
          700: '#654321',
          800: '#4A2C2A',
          900: '#2F1B1B',
        },
      },
    },
    dark: {
      palette: {
        primary: {
          50: '#2F1B1B',
          100: '#4A2C2A',
          200: '#654321',
          300: '#8B4513',
          400: '#A0522D',
          500: '#D2691E', // Lighter coffee brown for dark mode
          600: '#F4A460',
          700: '#DEB887',
          800: '#F5DEB3',
          900: '#FFF8DC',
        },
      },
    },
  },
});

// Mode toggle component
function ModeToggle() {
  const { mode, setMode } = useColorScheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const handleModeChange = () => {
    const modes = ['light', 'dark', 'system'];
    const currentIndex = modes.indexOf(mode);
    const nextIndex = (currentIndex + 1) % modes.length;
    setMode(modes[nextIndex]);
  };

  const getIcon = () => {
    switch (mode) {
      case 'light': return <Sun size={18} />;
      case 'dark': return <Moon size={18} />;
      default: return <Laptop size={18} />;
    }
  };

  return (
    <IconButton
      variant="outlined"
      size="sm"
      onClick={handleModeChange}
      sx={{ 
        position: 'absolute',
        top: 16,
        right: 16,
        borderRadius: 'sm'
      }}
    >
      {getIcon()}
    </IconButton>
  );
}

export default function LoginPage({ 
  onLogin, 
  onSignup, 
  onGitHubAuth, 
  loading = false, 
  error = '', 
  onClearError 
}) {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error && onClearError) {
      onClearError();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isSignUp) {
      onSignup(formData);
    } else {
      onLogin(formData);
    }
  };

  const handleGitHubAuth = () => {
    onGitHubAuth();
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <CssVarsProvider theme={theme}>
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, var(--joy-palette-primary-50) 0%, var(--joy-palette-primary-100) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 2,
          position: 'relative'
        }}
      >
        <ModeToggle />
        
        <Sheet
          variant="outlined"
          sx={{
            width: 400,
            py: 4,
            px: 3,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            borderRadius: 'lg',
            boxShadow: 'lg',
            backgroundColor: 'background.surface',
            border: '1px solid',
            borderColor: 'divider'
          }}
        >
          {/* Header */}
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <Coffee size={48} color="var(--joy-palette-primary-500)" />
            </Box>
            <Typography level="h3" component="h1" sx={{ mb: 1 }}>
              ☕ Coffee Rater
            </Typography>
            <Typography level="body-sm" color="neutral">
              {isSignUp 
                ? 'Join the community of coffee enthusiasts' 
                : 'Welcome back! Sign in to rate your favorite coffees'}
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert color="danger" variant="soft" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <Stack spacing={2}>
            <FormControl required>
              <FormLabel>Username</FormLabel>
              <Input
                name="username"
                type="text"
                placeholder="Enter your username"
                value={formData.username}
                onChange={handleInputChange}
                disabled={loading}
                sx={{ '--Input-focusedThickness': '2px' }}
              />
            </FormControl>

            <FormControl required>
              <FormLabel>Password</FormLabel>
              <Input
                name="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleInputChange}
                disabled={loading}
                endDecorator={
                  <IconButton
                    variant="plain"
                    size="sm"
                    onClick={togglePasswordVisibility}
                    sx={{ mr: -1 }}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </IconButton>
                }
                sx={{ '--Input-focusedThickness': '2px' }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSubmit(e);
                  }
                }}
              />
            </FormControl>

            <Button
              onClick={handleSubmit}
              loading={loading}
              fullWidth
              size="lg"
              disabled={!formData.username || !formData.password}
              sx={{ 
                mt: 2,
                bgcolor: 'primary.500',
                '&:hover': { bgcolor: 'primary.600' }
              }}
            >
              {isSignUp ? 'Create Account' : 'Sign In'}
            </Button>
          </Stack>

          {/* Divider */}
          <Divider sx={{ my: 2 }}>or</Divider>

          {/* GitHub OAuth Button */}
          <Button
            variant="outlined"
            fullWidth
            size="lg"
            startDecorator={<Github size={20} />}
            onClick={handleGitHubAuth}
            disabled={loading}
            sx={{
              borderColor: 'neutral.300',
              color: 'neutral.700',
              '&:hover': {
                borderColor: 'neutral.400',
                backgroundColor: 'neutral.50'
              }
            }}
          >
            Continue with GitHub
          </Button>

          {/* Toggle Sign Up/Sign In */}
          <Typography
            level="body-sm"
            sx={{ 
              alignSelf: 'center', 
              mt: 2,
              color: 'text.secondary'
            }}
          >
            {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
            <Link
              component="button"
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                if (onClearError) onClearError();
                setFormData({ username: '', password: '' });
              }}
              sx={{ fontWeight: 'md' }}
            >
              {isSignUp ? 'Sign in' : 'Sign up'}
            </Link>
          </Typography>

          {/* Footer */}
          <Typography 
            level="body-xs" 
            sx={{ 
              textAlign: 'center', 
              mt: 3, 
              color: 'text.tertiary' 
            }}
          >
            Discover, rate, and share your favorite coffee experiences
          </Typography>
        </Sheet>
      </Box>
    </CssVarsProvider>
  );
}