import { useEffect, useState } from 'react';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import DetailGrid from '../../components/ui/DetailGrid';
import Drawer from '../../components/ui/Drawer';
import EmptyState from '../../components/ui/EmptyState';
import ErrorState from '../../components/ui/ErrorState';
import FormField from '../../components/ui/FormField';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import Skeleton from '../../components/ui/Skeleton';
import Table from '../../components/ui/Table';
import { useAuth } from '../../hooks/useAuth';
import { listDistricts } from '../../services/complaintService';
import { listBusinesses } from '../../services/businessService';

function Businesses() {
  const { getAccessToken } = useAuth();
  const [businesses, setBusinesses] = useState(null);
  const [districts, setDistricts] = useState([]);
  const [query, setQuery] = useState('');
  const [districtId, setDistrictId] = useState('');
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    listDistricts(getAccessToken())
      .then(setDistricts)
      .catch(() => {});
  }, [getAccessToken]);

  useEffect(() => {
    const token = getAccessToken();
    const handle = setTimeout(() => {
      listBusinesses(token, { q: query || undefined, districtId: districtId || undefined, pageSize: 50 })
        .then(setBusinesses)
        .catch((err) => setError(err.message));
    }, 250);
    return () => clearTimeout(handle);
  }, [getAccessToken, query, districtId]);

  return (
    <ContentContainer>
      <PageHeader title="Businesses" description="Businesses recorded through citizen complaints, statewide." />

      <div className="flex flex-wrap gap-3">
        <FormField label="Search" htmlFor="business-search" className="w-64">
          <Input
            id="business-search"
            placeholder="Business name…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </FormField>
        <FormField label="District" htmlFor="business-district-filter" className="w-56">
          <Select id="business-district-filter" value={districtId} onChange={(event) => setDistrictId(event.target.value)}>
            <option value="">All districts</option>
            {districts.map((district) => (
              <option key={district.id} value={district.id}>
                {district.name}
              </option>
            ))}
          </Select>
        </FormField>
      </div>

      {error && <ErrorState message={error} />}

      {!businesses && !error && <Skeleton.List rows={5} />}

      {businesses && businesses.length === 0 && <EmptyState title="No businesses match these filters." />}

      {businesses && businesses.length > 0 && (
        <Table>
          <Table.Head>
            <tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>License</Table.Th>
              <Table.Th>Address</Table.Th>
              <Table.Th>Status</Table.Th>
            </tr>
          </Table.Head>
          <Table.Body>
            {businesses.map((business) => (
              <Table.Tr
                key={business.id}
                className="cursor-pointer"
                onClick={() => setSelected(business)}
              >
                <Table.Td className="font-medium text-slate-900">{business.business_name}</Table.Td>
                <Table.Td>{business.business_type || '—'}</Table.Td>
                <Table.Td>{business.license_number || '—'}</Table.Td>
                <Table.Td className="max-w-xs truncate">{business.address}</Table.Td>
                <Table.Td>{business.is_active ? 'Active' : 'Inactive'}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Body>
        </Table>
      )}

      <Drawer open={Boolean(selected)} onClose={() => setSelected(null)} title={selected?.business_name}>
        {selected && (
          <DetailGrid>
            <dt>Type</dt>
            <dd>{selected.business_type || '—'}</dd>
            <dt>License number</dt>
            <dd>{selected.license_number || '—'}</dd>
            <dt>Address</dt>
            <dd>{selected.address}</dd>
            <dt>Contact phone</dt>
            <dd>{selected.contact_phone || '—'}</dd>
            <dt>Status</dt>
            <dd>{selected.is_active ? 'Active' : 'Inactive'}</dd>
          </DetailGrid>
        )}
      </Drawer>
    </ContentContainer>
  );
}

export default Businesses;
