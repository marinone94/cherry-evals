import { useAuth } from '../lib/AuthContext';

const POLAR_PRO_CHECKOUT_URL = import.meta.env.VITE_POLAR_PRO_CHECKOUT_URL || '';
const POLAR_ULTRA_CHECKOUT_URL = import.meta.env.VITE_POLAR_ULTRA_CHECKOUT_URL || '';

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    features: [
      'Keyword search (30/min)',
      '50 semantic/hybrid searches per day',
      '10 collections, 1,000 examples each',
      'JSON / JSONL / CSV export',
      '1 API key',
      'MCP access (Free limits)',
    ],
    blocked: [
      'Intelligent search (LLM-powered)',
      'Agentic ingestion & export',
      'Langfuse export',
    ],
    cta: 'Current plan',
    highlighted: false,
    checkoutUrl: null,
  },
  {
    name: 'Pro',
    price: '$19',
    period: '/month',
    features: [
      'Keyword search (120/min)',
      'Unlimited semantic/hybrid search',
      '180 LLM calls per day (Flash)',
      'Unlimited collections & examples',
      'All export formats incl. Langfuse',
      'Agentic ingestion & export',
      '10 API keys',
      'MCP access (Pro limits)',
    ],
    blocked: [],
    cta: 'Upgrade to Pro',
    highlighted: false,
    checkoutUrl: POLAR_PRO_CHECKOUT_URL,
  },
  {
    name: 'Ultra',
    price: '$49',
    period: '/month',
    features: [
      'Everything in Pro',
      '300 LLM calls per day (Pro + Flash)',
      'Priority support',
      '10 API keys',
    ],
    blocked: [],
    cta: 'Upgrade to Ultra',
    highlighted: true,
    checkoutUrl: POLAR_ULTRA_CHECKOUT_URL,
  },
];

export default function PricingPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-5xl mx-auto mt-8">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900">Plans & Pricing</h1>
        <p className="mt-2 text-gray-600">
          Free for exploration. Pro for LLM-powered features. Ultra for maximum capacity.
        </p>
        <p className="mt-3 inline-block px-4 py-1.5 bg-purple-50 text-purple-700 rounded-full text-sm font-medium">
          Start with a free 1-week Ultra trial
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`rounded-lg border p-6 ${
              plan.highlighted
                ? 'border-purple-300 bg-purple-50/30 ring-1 ring-purple-200'
                : 'border-gray-200 bg-white'
            }`}
          >
            <h2 className="text-xl font-bold text-gray-900">{plan.name}</h2>
            <p className="mt-1">
              <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
              <span className="text-gray-500 ml-1">{plan.period}</span>
            </p>

            <ul className="mt-6 space-y-2">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-green-500 mt-0.5">&#10003;</span>
                  {f}
                </li>
              ))}
              {plan.blocked.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-gray-400">
                  <span className="mt-0.5">&#10007;</span>
                  {f}
                </li>
              ))}
            </ul>

            <div className="mt-6">
              {plan.checkoutUrl ? (
                <a
                  href={plan.checkoutUrl}
                  className={`block w-full text-center py-2 rounded-md font-medium ${
                    plan.highlighted
                      ? 'bg-purple-500 text-white hover:bg-purple-600'
                      : 'bg-red-500 text-white hover:bg-red-600'
                  }`}
                >
                  {plan.cta}
                </a>
              ) : plan.name !== 'Free' ? (
                <span className="block w-full text-center py-2 bg-gray-100 text-gray-400 rounded-md font-medium">
                  Coming soon
                </span>
              ) : (
                <span className="block w-full text-center py-2 bg-gray-100 text-gray-500 rounded-md font-medium">
                  {user ? plan.cta : 'Sign up free'}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
