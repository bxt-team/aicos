'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'
import WaitlistSignup from './WaitlistSignup'

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center pt-20 overflow-hidden">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-secondary-50" />
      
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            repeatType: 'reverse',
          }}
          className="absolute -top-20 -left-20 w-96 h-96 bg-primary-200 rounded-full opacity-20 blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            rotate: [0, -90, 0],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            repeatType: 'reverse',
          }}
          className="absolute -bottom-20 -right-20 w-96 h-96 bg-secondary-200 rounded-full opacity-20 blur-3xl"
        />
      </div>

      <div className="relative max-w-7xl mx-auto container-padding">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-heading font-bold text-secondary-900 leading-tight">
              Build Your Company with{' '}
              <span className="gradient-text">AI Departments</span>
            </h1>
            
            <p className="mt-6 text-lg md:text-xl text-secondary-600 leading-relaxed">
              Built for <span className="font-semibold text-secondary-800">solo founders</span>, 
              <span className="font-semibold text-secondary-800"> small AI-first teams</span>, and 
              <span className="font-semibold text-secondary-800"> digital entrepreneurs</span> - 
              set up entire departments powered by AI agents. Define your projects and key results, 
              then let AI teams do the work while you focus on strategy.
            </p>

            {/* Replace CTA buttons with Waitlist Signup for ProductHunt launch */}
            <WaitlistSignup variant="hero" />

            <div className="mt-12 grid grid-cols-3 gap-4 max-w-lg">
              <div>
                <div className="text-3xl font-bold text-secondary-800">100+</div>
                <div className="text-sm text-secondary-600">AI Agents Available</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-secondary-800">24/7</div>
                <div className="text-sm text-secondary-600">Autonomous Work</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-secondary-800">10x</div>
                <div className="text-sm text-secondary-600">Productivity Boost</div>
              </div>
            </div>
          </motion.div>

          {/* Dashboard Preview */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="relative rounded-2xl overflow-hidden shadow-2xl">
              <div className="aspect-[4/3] bg-gradient-to-br from-gray-900 to-gray-800 p-8">
                {/* Mock Company Dashboard */}
                <div className="bg-white/10 backdrop-blur rounded-lg p-4 mb-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-white font-semibold">Your AI Company</div>
                    <div className="flex gap-2">
                      <div className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm">Active</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-white/10 rounded p-3">
                      <div className="text-sm text-gray-300 mb-1">Marketing</div>
                      <div className="text-lg font-semibold text-white">5 Agents</div>
                    </div>
                    <div className="bg-white/10 rounded p-3">
                      <div className="text-sm text-gray-300 mb-1">Sales</div>
                      <div className="text-lg font-semibold text-white">3 Agents</div>
                    </div>
                    <div className="bg-white/10 rounded p-3">
                      <div className="text-sm text-gray-300 mb-1">Support</div>
                      <div className="text-lg font-semibold text-white">2 Agents</div>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                    <div className="text-sm text-gray-300 mb-2">Active Projects</div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                        <span className="text-white text-sm">Q4 Campaign</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                        <span className="text-white text-sm">Product Launch</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                        <span className="text-white text-sm">SEO Optimization</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white/10 backdrop-blur rounded-lg p-4">
                    <div className="text-sm text-gray-300 mb-2">Key Results</div>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-xs text-gray-300 mb-1">
                          <span>Revenue</span>
                          <span>87%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div className="bg-green-500 h-2 rounded-full" style={{width: '87%'}}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-gray-300 mb-1">
                          <span>Leads</span>
                          <span>124%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{width: '100%'}}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Floating Elements */}
              <motion.div
                animate={{ y: [-10, 10, -10] }}
                transition={{ duration: 4, repeat: Infinity }}
                className="absolute -top-4 -right-4 bg-white rounded-lg shadow-lg p-3"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium">AI Agent Active</span>
                </div>
              </motion.div>
              
              <motion.div
                animate={{ y: [10, -10, 10] }}
                transition={{ duration: 5, repeat: Infinity }}
                className="absolute -bottom-4 -left-4 bg-white rounded-lg shadow-lg p-3"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium">10 AI Departments</span>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

export default Hero