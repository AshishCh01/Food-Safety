import { useEffect, useState } from 'react';
import { PlusCircle } from 'lucide-react';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Alert from '../../components/ui/Alert';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';
import Pagination from '../../components/ui/Pagination';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import Table from '../../components/ui/Table';
import Tabs from '../../components/ui/Tabs';
import { useAuth } from '../../hooks/useAuth';
import { formatDate } from '../../utils/formatters';
import { listDistricts } from '../../services/complaintService';
import { createStaff, listUsers, updateUserStatus } from '../../services/staffService';

const ROLE_TABS = [
  { value: 'district_officer', label: 'District Officers' },
  { value: 'inspector', label: 'Inspectors' },
];

const PAGE_SIZE = 20;

const INITIAL_FORM = {
  fullName: '',
  email: '',
  password: '',
  phone: '',
  role: 'inspector',
  districtId: '',
  employeeCode: '',
  designation: '',
};

function StaffManagement() {
  const { getAccessToken } = useAuth();
  const [role, setRole] = useState('district_officer');
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(null);
  const [districts, setDistricts] = useState([]);
  const [error, setError] = useState(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);
  const [createError, setCreateError] = useState(null);
  const [isCreating, setIsCreating] = useState(false);

  const [statusTarget, setStatusTarget] = useState(null);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  function load() {
    const token = getAccessToken();
    listUsers(token, { role, page, pageSize: PAGE_SIZE })
      .then(setResult)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [getAccessToken, role, page]);

  useEffect(() => {
    listDistricts(getAccessToken())
      .then(setDistricts)
      .catch(() => {});
  }, [getAccessToken]);

  function updateField(field) {
    return (event) => setForm((prev) => ({ ...prev, [field]: event.target.value }));
  }

  function openCreate() {
    setForm({ ...INITIAL_FORM, role });
    setCreateError(null);
    setIsCreateOpen(true);
  }

  async function handleCreate(event) {
    event.preventDefault();
    setCreateError(null);
    setIsCreating(true);
    try {
      await createStaff(form, getAccessToken());
      setIsCreateOpen(false);
      load();
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setIsCreating(false);
    }
  }

  async function handleConfirmStatusChange() {
    setIsUpdatingStatus(true);
    try {
      await updateUserStatus(statusTarget.id, !statusTarget.is_active, getAccessToken());
      setStatusTarget(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUpdatingStatus(false);
    }
  }

  return (
    <ContentContainer>
      <PageHeader
        title="Staff"
        description="District officers and inspectors provisioned across Maharashtra."
        actions={
          <Button onClick={openCreate}>
            <PlusCircle className="size-4" aria-hidden="true" />
            Create staff account
          </Button>
        }
      />

      <Tabs
        items={ROLE_TABS}
        value={role}
        onChange={(value) => {
          setRole(value);
          setPage(1);
        }}
      />

      {error && <ErrorState message={error} />}

      {!result && !error && <Skeleton.List rows={4} />}

      {result && result.items.length === 0 && <EmptyState title="No staff accounts found for this role." />}

      {result && result.items.length > 0 && (
        <Table>
          <Table.Head>
            <tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Email</Table.Th>
              <Table.Th>Phone</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Joined</Table.Th>
              <Table.Th>Action</Table.Th>
            </tr>
          </Table.Head>
          <Table.Body>
            {result.items.map((user) => (
              <Table.Tr key={user.id}>
                <Table.Td className="font-medium text-slate-900">{user.full_name}</Table.Td>
                <Table.Td>{user.email}</Table.Td>
                <Table.Td>{user.phone || '—'}</Table.Td>
                <Table.Td>
                  <Badge tone={user.is_active ? 'success' : 'neutral'}>{user.is_active ? 'Active' : 'Disabled'}</Badge>
                </Table.Td>
                <Table.Td>{formatDate(user.created_at)}</Table.Td>
                <Table.Td>
                  <Button variant="secondary" size="sm" onClick={() => setStatusTarget(user)}>
                    {user.is_active ? 'Disable' : 'Enable'}
                  </Button>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Body>
        </Table>
      )}

      {result && <Pagination page={page} pageSize={PAGE_SIZE} total={result.total} onPageChange={setPage} />}

      <Modal open={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create staff account">
        <form onSubmit={handleCreate} className="flex flex-col gap-4">
          <FormField label="Full name" htmlFor="staff-full-name" required>
            <Input id="staff-full-name" value={form.fullName} onChange={updateField('fullName')} required />
          </FormField>
          <FormField label="Email" htmlFor="staff-email" required>
            <Input id="staff-email" type="email" value={form.email} onChange={updateField('email')} required />
          </FormField>
          <FormField label="Temporary password" htmlFor="staff-password" required>
            <Input
              id="staff-password"
              type="password"
              minLength={8}
              value={form.password}
              onChange={updateField('password')}
              required
            />
          </FormField>
          <FormField label="Phone" htmlFor="staff-phone" hint="Optional">
            <Input id="staff-phone" value={form.phone} onChange={updateField('phone')} />
          </FormField>
          <FormField label="Role" htmlFor="staff-role" required>
            <Select id="staff-role" value={form.role} onChange={updateField('role')} required>
              <option value="inspector">Inspector</option>
              <option value="district_officer">District Officer</option>
            </Select>
          </FormField>
          <FormField label="District" htmlFor="staff-district" required>
            <Select id="staff-district" value={form.districtId} onChange={updateField('districtId')} required>
              <option value="">Select a district</option>
              {districts.map((district) => (
                <option key={district.id} value={district.id}>
                  {district.name}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Employee code" htmlFor="staff-employee-code" required>
            <Input id="staff-employee-code" value={form.employeeCode} onChange={updateField('employeeCode')} required />
          </FormField>
          <FormField label="Designation" htmlFor="staff-designation" hint="Optional">
            <Input id="staff-designation" value={form.designation} onChange={updateField('designation')} />
          </FormField>
          {createError && <Alert tone="danger">{createError}</Alert>}
          <Button type="submit" loading={isCreating} className="self-start">
            {isCreating ? 'Creating…' : 'Create staff account'}
          </Button>
        </form>
      </Modal>

      <ConfirmDialog
        open={Boolean(statusTarget)}
        onClose={() => setStatusTarget(null)}
        onConfirm={handleConfirmStatusChange}
        loading={isUpdatingStatus}
        title={statusTarget?.is_active ? 'Disable account?' : 'Enable account?'}
        description={
          statusTarget
            ? `${statusTarget.full_name} will ${statusTarget.is_active ? 'no longer' : 'once again'} be able to log in.`
            : ''
        }
        confirmLabel={statusTarget?.is_active ? 'Disable' : 'Enable'}
        tone={statusTarget?.is_active ? 'danger' : 'primary'}
      />
    </ContentContainer>
  );
}

export default StaffManagement;
