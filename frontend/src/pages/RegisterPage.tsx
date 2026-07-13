import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { UserRole } from '@/types';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>(UserRole.ANALYST);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register({
        full_name: fullName,
        email,
        password,
        role,
      });
      navigate('/dashboard', { replace: true });
    } catch {
      setError('Could not create your account. The email may already exist.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Sparkles className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            Create your account
          </h1>
          <p className="text-sm text-slate-500">
            Get started with autonomous analytics
          </p>
        </div>

        <form
          onSubmit={onSubmit}
          className="surface space-y-4 rounded-xl p-6 shadow-card"
        >
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
              {error}
            </div>
          )}
          <Input
            label="Full name"
            name="full_name"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Jane Doe"
          />
          <Input
            label="Email"
            type="email"
            name="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
          <Input
            label="Password"
            type="password"
            name="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            >
              <option value={UserRole.ANALYST}>Analyst</option>
              <option value={UserRole.VIEWER}>Viewer</option>
              <option value={UserRole.ADMIN}>Admin</option>
            </select>
          </div>
          <Button type="submit" loading={loading} className="w-full">
            Create account
          </Button>
          <p className="text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-brand-600">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
