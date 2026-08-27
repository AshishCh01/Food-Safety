import { useEffect, useState } from 'react';
import { getHealth } from '../../services/api';

function Home() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err.message));
  }, []);

  let badge = <span className="status-badge loading">Checking backend...</span>;
  if (error) {
    badge = <span className="status-badge error">Backend unreachable</span>;
  } else if (health) {
    badge = (
      <span className="status-badge ok">
        Backend {health.status} - DB {health.database}
      </span>
    );
  }

  return (
    <section>
      <h1>Maharashtra Food Safety Platform</h1>
      <p>Project foundation is running.</p>
      {badge}
    </section>
  );
}

export default Home;
