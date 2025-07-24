# AICOS - Marketing Website

This is the marketing website for AICOS, built with Next.js 14, TypeScript, and Tailwind CSS. AICOS is where AI runs your business.

## Features

- Modern, responsive design
- Smooth animations with Framer Motion
- SEO optimized
- Performance optimized with Next.js
- Type-safe with TypeScript
- Beautiful UI components

## Getting Started

1. Install dependencies:
```bash
cd website
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) to view the website.

## Project Structure

```
website/
├── app/              # Next.js app directory
│   ├── layout.tsx    # Root layout
│   ├── page.tsx      # Home page
│   └── globals.css   # Global styles
├── components/       # React components
│   ├── Navbar.tsx    # Navigation bar
│   ├── Hero.tsx      # Hero section
│   ├── Features.tsx  # Features section
│   ├── HowItWorks.tsx # How it works section
│   ├── Pricing.tsx   # Pricing plans
│   ├── Testimonials.tsx # Customer testimonials
│   ├── CTA.tsx       # Call to action
│   └── Footer.tsx    # Footer
├── public/           # Static assets
└── package.json      # Dependencies
```

## Building for Production

To create a production build:

```bash
npm run build
npm run start
```

## Deployment

The website can be deployed to any platform that supports Next.js:

- Vercel (recommended)
- Netlify
- AWS Amplify
- Docker

## Environment Variables

Create a `.env.local` file for environment variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Customization

- Update colors in `tailwind.config.js`
- Modify content in component files
- Add new pages in the `app` directory
- Update metadata in `app/layout.tsx`

## About AICOS

AICOS is an AI-powered business automation platform that helps businesses create content, manage workflows, and scale operations with intelligent AI agents working 24/7.