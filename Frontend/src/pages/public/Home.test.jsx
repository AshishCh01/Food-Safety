import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Home from './Home';

describe('Home', () => {
  it('renders the platform heading and backend status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'ok', database: 'connected' }),
        }),
      ),
    );

    render(<Home />);

    expect(
      screen.getByText('Maharashtra Food Safety Platform'),
    ).toBeInTheDocument();

    expect(await screen.findByText(/Backend ok/)).toBeInTheDocument();
  });
});
