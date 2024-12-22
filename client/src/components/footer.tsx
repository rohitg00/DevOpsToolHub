export function Footer() {
  return (
    <footer className="bg-background border-t">
      <div className="container mx-auto py-8 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-semibold text-lg mb-4">Join Our Community</h3>
            <p className="text-muted-foreground mb-4">
              Connect with DevOps professionals, share knowledge, and stay updated with the latest trends.
            </p>
            <a 
              href="https://x.com/i/communities/1523681883384549376"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600"
            >
              Twitter DevOps Community →
            </a>
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-4">Resources</h3>
            <ul className="space-y-2">
              <li>
                <a 
                  href="https://www.devopscommunity.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground"
                >
                  DevOps Community Portal
                </a>
              </li>
              <li>
                <a 
                  href="https://interview.devopscommunity.in/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Practice DevOps Interviews
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-4">About</h3>
            <p className="text-muted-foreground">
              DevOps Tools Directory is a community-driven project to help DevOps engineers find and compare the best tools for their workflow.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
} 