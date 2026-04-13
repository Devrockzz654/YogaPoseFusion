import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders the public landing page", () => {
  localStorage.clear();
  render(<App />);
  expect(
    screen.getByText(/Get age-aware asana recommendations and real-time correction/i)
  ).toBeInTheDocument();
});
