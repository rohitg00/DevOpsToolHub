import { Route, Switch } from "wouter";
import { Home } from "./pages/home";
import { ToolPage } from "./pages/tool";
import { Header } from "@/components/header";
import { Footer } from "@/components/footer";

function App() {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header />
      <main className="flex-1">
        <Switch>
          <Route path="/" component={Home} />
          <Route path="/tool/:name">
            {params => <ToolPage params={params} />}
          </Route>
        </Switch>
      </main>
      <Footer />
    </div>
  );
}

export default App;
