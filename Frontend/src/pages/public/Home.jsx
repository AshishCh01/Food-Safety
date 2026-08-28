import { useEffect, useState } from 'react';
import { FileWarning, MapPinned, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getHealth } from '../../services/api';
import Badge from '../../components/ui/Badge';

const STEPS = [
  {
    icon: FileWarning,
    title: 'Report a concern',
    description: 'Describe the issue, attach photos, and pin the location of the business.',
  },
  {
    icon: MapPinned,
    title: 'Routed to your district',
    description: 'Your complaint reaches the food safety officer responsible for that area automatically.',
  },
  {
    icon: ShieldCheck,
    title: 'Reviewed and resolved',
    description: 'Track verification, inspection, and outcome from your dashboard at every step.',
  },
];

function Home() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  let statusBadge = <Badge tone="neutral">Checking backend…</Badge>;
  if (error) {
    statusBadge = <Badge tone="danger">Backend unreachable</Badge>;
  } else if (health) {
    statusBadge = (
      <Badge tone="success">
        Backend {health.status} - DB {health.database}
      </Badge>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
      <div className="max-w-2xl">
        <p className="text-sm font-medium text-brand-700">Government of Maharashtra</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
          Maharashtra Food Safety Platform
        </h1>
        <p className="mt-3 text-base text-slate-600">
          Report suspected food-safety violations, track their progress, and help district officers and inspectors
          verify and resolve them &mdash; with AI-assisted triage and investigation support along the way.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Link
            to="/register"
            className="inline-flex h-10 items-center justify-center rounded-md border border-brand-700 bg-brand-700 px-5 text-sm font-medium text-white hover:bg-brand-800"
          >
            Report a concern
          </Link>
          <Link
            to="/login"
            className="inline-flex h-10 items-center justify-center rounded-md border border-slate-300 bg-white px-5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Staff log in
          </Link>
        </div>
      </div>

      <div className="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {STEPS.map((step) => (
          <div key={step.title} className="rounded-lg border border-slate-200 bg-white p-4">
            <step.icon className="size-5 text-brand-700" aria-hidden="true" />
            <h2 className="mt-2 text-sm font-semibold text-slate-900">{step.title}</h2>
            <p className="mt-1 text-sm text-slate-500">{step.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-10">{statusBadge}</div>
    </div>
  );
}

export default Home;
