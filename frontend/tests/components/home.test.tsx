import { render, screen } from '@testing-library/react';
import Home from '../../app/page';

// Verify that the Home page renders the dashboard heading
describe('Home component', () => {
  it('renders heading', () => {
    render(<Home />);
    expect(
      screen.getByRole('heading', { name: /crypto analytics dashboard/i }),
    ).toBeInTheDocument();
  });
});
