import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../../services/authService';
import Alert from '../../components/ui/Alert';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';

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
    <div className="mx-auto max-w-sm px-4 py-16 sm:px-0">
      <h1 className="mb-5 text-xl font-semibold text-slate-900">Create a citizen account</h1>
      <Card>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <FormField label="Full name" htmlFor="register-name" required>
            <Input id="register-name" value={form.fullName} onChange={updateField('fullName')} required />
          </FormField>
          <FormField label="Email" htmlFor="register-email" required>
            <Input
              id="register-email"
              type="email"
              value={form.email}
              onChange={updateField('email')}
              required
            />
          </FormField>
          <FormField label="Phone" htmlFor="register-phone" hint="Optional">
            <Input id="register-phone" value={form.phone} onChange={updateField('phone')} />
          </FormField>
          <FormField label="Password" htmlFor="register-password" required>
            <Input
              id="register-password"
              type="password"
              minLength={8}
              value={form.password}
              onChange={updateField('password')}
              required
            />
          </FormField>
          {error && <Alert tone="danger">{error}</Alert>}
          <Button type="submit" loading={isSubmitting} className="w-full">
            {isSubmitting ? 'Creating account…' : 'Register'}
          </Button>
        </form>
      </Card>
      <p className="mt-4 text-center text-sm text-slate-600">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-brand-700 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

export default Register;
