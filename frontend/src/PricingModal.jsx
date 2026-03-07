import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Zap, Rocket, Crown, X, Check } from 'lucide-react';

const tiers = [
    {
        name: 'free',
        displayName: 'Free',
        price: '$0',
        period: '',
        icon: ShieldCheck,
        color: '#6b7280',
        tokens: '10,000',
        features: [
            '10,000 tokens/day',
            'Basic compliance queries',
            'Community support',
        ],
        cta: 'Current Plan',
        disabled: true,
    },
    {
        name: 'pro',
        displayName: 'Pro',
        price: '$29',
        period: '/mo',
        icon: Zap,
        color: '#6366f1',
        tokens: '100,000',
        popular: true,
        features: [
            '100,000 tokens/day',
            'PDF document analysis',
            'Priority support',
            'Query history',
        ],
        cta: 'Subscribe',
        disabled: false,
    },
    {
        name: 'max',
        displayName: 'Max',
        price: '$99',
        period: '/mo',
        icon: Rocket,
        color: '#8b5cf6',
        tokens: '500,000',
        features: [
            '500,000 tokens/day',
            'Unlimited PDF analysis',
            'Dedicated support',
            'API access',
            'Team sharing',
        ],
        cta: 'Subscribe',
        disabled: false,
    },
    {
        name: 'elite',
        displayName: 'Elite',
        price: '$299',
        period: '/mo',
        icon: Crown,
        color: '#f59e0b',
        tokens: 'Unlimited',
        features: [
            'Unlimited tokens',
            'Custom compliance rules',
            'SLA guarantee',
            'Dedicated account manager',
            'Custom integrations',
        ],
        cta: 'Subscribe',
        disabled: false,
    },
];

function PricingModal({ isOpen, onClose, currentTier, onSubscribe }) {
    if (!isOpen) return null;

    const handleSubscribe = async (tierName) => {
        if (onSubscribe) {
            await onSubscribe(tierName);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    className="pricing-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                >
                    <motion.div
                        className="pricing-modal glass-panel"
                        initial={{ opacity: 0, scale: 0.9, y: 30 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 30 }}
                        transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button className="pricing-close-btn" onClick={onClose}>
                            <X size={20} />
                        </button>

                        <div className="pricing-header">
                            <h2>You've reached your daily limit</h2>
                            <p>Upgrade your plan to continue using compliance.chat</p>
                        </div>

                        <div className="pricing-grid">
                            {tiers.map((tier) => {
                                const Icon = tier.icon;
                                const isCurrent = tier.name === currentTier;
                                const isUpgrade = !isCurrent && !tier.disabled;

                                return (
                                    <div
                                        key={tier.name}
                                        className={`pricing-card ${tier.popular ? 'popular' : ''} ${isCurrent ? 'current' : ''}`}
                                    >
                                        {tier.popular && (
                                            <div className="popular-badge">Most Popular</div>
                                        )}

                                        <div className="pricing-card-header">
                                            <div
                                                className="pricing-icon"
                                                style={{ background: `${tier.color}20`, color: tier.color }}
                                            >
                                                <Icon size={24} />
                                            </div>
                                            <h3>{tier.displayName}</h3>
                                            <div className="pricing-amount">
                                                <span className="price">{tier.price}</span>
                                                <span className="period">{tier.period}</span>
                                            </div>
                                            <div className="pricing-tokens">{tier.tokens} tokens/day</div>
                                        </div>

                                        <ul className="pricing-features">
                                            {tier.features.map((feature, i) => (
                                                <li key={i}>
                                                    <Check size={14} style={{ color: tier.color }} />
                                                    <span>{feature}</span>
                                                </li>
                                            ))}
                                        </ul>

                                        <button
                                            className={`pricing-cta ${isUpgrade ? 'upgrade' : ''}`}
                                            style={
                                                isUpgrade
                                                    ? { background: tier.color, borderColor: tier.color }
                                                    : {}
                                            }
                                            disabled={isCurrent}
                                            onClick={() => isUpgrade && handleSubscribe(tier.name)}
                                        >
                                            {isCurrent ? 'Current Plan' : tier.cta}
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

export default PricingModal;
