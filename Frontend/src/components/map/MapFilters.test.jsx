import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import MapFilters from './MapFilters';

const CATEGORIES = [{ id: 'cat-1', name: 'Expired Food' }];
const INITIAL_VALUE = { status: '', priority: '', categoryId: '', dateFrom: '', dateTo: '' };

describe('MapFilters', () => {
  it('renders the category options passed in', () => {
    render(<MapFilters categories={CATEGORIES} value={INITIAL_VALUE} onChange={() => {}} />);

    expect(screen.getByRole('option', { name: 'Expired Food' })).toBeInTheDocument();
  });

  it('calls onChange with the updated field when a filter changes', () => {
    const onChange = vi.fn();
    render(<MapFilters categories={CATEGORIES} value={INITIAL_VALUE} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText(/priority/i), { target: { value: 'high' } });

    expect(onChange).toHaveBeenCalledWith({ ...INITIAL_VALUE, priority: 'high' });
  });

  it('preserves other filter values when one changes', () => {
    const onChange = vi.fn();
    const value = { ...INITIAL_VALUE, status: 'verified' };
    render(<MapFilters categories={CATEGORIES} value={value} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText(/category/i), { target: { value: 'cat-1' } });

    expect(onChange).toHaveBeenCalledWith({ ...value, categoryId: 'cat-1' });
  });
});
