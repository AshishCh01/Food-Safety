import Alert from './Alert';

/** Page/section-level fetch failure. Renders as an alert (role="alert") so
 * it's reachable the same way the old `.form-error` paragraphs were. */
function ErrorState({ message = 'Something went wrong. Please try again.', className }) {
  return (
    <Alert tone="danger" className={className}>
      {message}
    </Alert>
  );
}

export default ErrorState;
