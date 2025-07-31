'use client'

import { motion } from 'framer-motion'
import { useInView } from 'react-intersection-observer'
import Link from 'next/link'
import WaitlistSignup from './WaitlistSignup'

const CTA = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  })

  return (
    <section className="section-padding bg-gradient-to-br from-primary-600 to-secondary-600 text-white">
      <div className="max-w-4xl mx-auto container-padding text-center">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-bold mb-6">
            Ready to Build Your AI Company?
          </h2>
          <p className="text-lg md:text-xl opacity-90 mb-8 max-w-2xl mx-auto">
            Join innovative founders and teams who are building the future with AI departments.
          </p>
          
          {/* Replace CTAs with waitlist for ProductHunt launch */}
          <div className="max-w-lg mx-auto">
            <WaitlistSignup variant="inline" />
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default CTA