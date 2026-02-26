import React from 'react';
import { motion } from 'framer-motion';

export const AppLayout = ({ children, className = '' }) => (
  <div className={`page-shell ${className}`}>
    <div className="app-container">{children}</div>
  </div>
);

export const PageHeader = ({ title, description, action }) => (
  <div className="mb-10 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
    <div className="space-y-2">
      <h1 className="headline-1">{title}</h1>
      {description ? <p className="body-text">{description}</p> : null}
    </div>
    {action ? <div className="shrink-0">{action}</div> : null}
  </div>
);

export const StaggerGrid = ({ children, className = '' }) => (
  <motion.div
    initial="hidden"
    animate="visible"
    variants={{
      hidden: {},
      visible: {
        transition: {
          staggerChildren: 0.08
        }
      }
    }}
    className={className}
  >
    {children}
  </motion.div>
);

export const StaggerItem = ({ children, className = '' }) => (
  <motion.div
    variants={{
      hidden: { opacity: 0, y: 8 },
      visible: { opacity: 1, y: 0 }
    }}
    transition={{ duration: 0.35, ease: 'easeOut' }}
    className={className}
  >
    {children}
  </motion.div>
);
