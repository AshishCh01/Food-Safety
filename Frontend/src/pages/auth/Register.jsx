import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../../services/authService';

function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ fullName: '', email: '', phone: '', password: '' });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(form);
      navigate('/login', { replace: true, state: { registered: true } });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="auth-page">
      <h1>Create a citizen account</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <label htmlFor="register-name">
          Full name
          <input id="register-name" value={form.fullName} onChange={updateField('fullName')} required />
        </label>
        <label htmlFor="register-email">
          Email
          <input
            id="register-email"
            type="email"
            value={form.email}
            onChange={updateField('email')}
            required
          />
        </label>
        <label htmlFor="register-phone">
          Phone (optional)
          <input id="register-phone" value={form.phone} onChange={updateField('phone')} />
        </label>
        <label htmlFor="register-password">
          Password
          <input
            id="register-password"
            type="password"
            minLength={8}
            value={form.password}
            onChange={updateField('password')}
            required
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Register'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  );
}

export default Register;
