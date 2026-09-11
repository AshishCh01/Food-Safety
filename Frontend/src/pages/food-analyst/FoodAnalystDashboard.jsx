import { Link } from 'react-router-dom';
import ContentContainer from '../../components/layout/ContentContainer';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

function FoodAnalystDashboard() {
  return (
    <ContentContainer>
      <PageHeader title="Food Analyst Dashboard" />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <Card.Header>
            <Card.Title>Sample Review</Card.Title>
          </Card.Header>
          <p className="text-sm text-slate-700 mb-4">
            Review samples assigned to you, mark them as received, and submit analysis results.
          </p>
          <Link to="/food-analyst/samples">
            <Button>View Samples</Button>
          </Link>
        </Card>
      </div>
    </ContentContainer>
  );
}

export default FoodAnalystDashboard;
