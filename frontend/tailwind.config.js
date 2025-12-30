/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Colores corporativos BDO
        primary: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc8fb',
          400: '#36aaf5',
          500: '#0c8de6',
          600: '#006fc4',
          700: '#01599f',
          800: '#064b83',
          900: '#0a3f6d',
          950: '#072849',
        },
        secondary: {
          50: '#f5f7fa',
          100: '#ebeef3',
          200: '#d2dae5',
          300: '#aab9ce',
          400: '#7c93b2',
          500: '#5b7699',
          600: '#475f7f',
          700: '#3a4d67',
          800: '#334257',
          900: '#2e3949',
          950: '#1e2530',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
