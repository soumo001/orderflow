import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  BarChart3, Boxes, ChevronDown, Home, LogOut, Menu, Package, Search, ShoppingBag,
  ShoppingCart, Sparkles, Truck, Users, X,
} from "lucide-react";
import { createRoot } from "react-dom/client";

import { request } from "./api";
import "./styles.css";
import "./polish.css";

type Product = {
  id: string; name: string; sku: string; category: string; price: string;
  description?: string; image_url?: string; available_quantity: number;
};
type User = { id: string; email: string; first_name: string; last_name: string; roles: string[] };
type Order = { id: string; status: string; total: string; subtotal: string; created_at: string; items: { product_id: string; quantity: number }[] };
type Inventory = { product_id: string; quantity: number; reserved_quantity: number; available_quantity: number; low_stock_threshold: number };
type Page = "home" | "catalogue" | "cart" | "orders" | "operations" | "inventory";

function App() {
  const [page, setPage] = useState<Page>((location.hash.slice(1) as Page) || "home");
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [cart, setCart] = useState<Record<string, number>>({});
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<Record<string, number | string> | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState("created_at");
  const [authOpen, setAuthOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebar, setSidebar] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const cartItems = useMemo(() => products.filter((product) => cart[product.id]), [products, cart]);
  const total = cartItems.reduce((sum, product) => sum + Number(product.price) * cart[product.id], 0);
  const categories = [...new Set(products.map((product) => product.category))].sort();

  function navigate(next: Page) {
    setPage(next);
    location.hash = next;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function loadProducts() {
    const params = new URLSearchParams({ page_size: "100", sort, descending: "true" });
    if (search.trim()) params.set("search", search.trim());
    if (category) params.set("category", category);
    setProducts((await request<{ items: Product[] }>(`/products?${params}`)).items);
  }

  async function loadSession() {
    if (!localStorage.getItem("orderflow_access")) return;
    try {
      const current = await request<User>("/auth/me");
      setUser(current);
      setOrders(await request<Order[]>("/orders"));
      if (current.roles.includes("ADMIN")) setDashboard(await request("/admin/dashboard"));
      if (current.roles.some((role) => ["ADMIN", "INVENTORY_MANAGER"].includes(role))) setInventory(await request<Inventory[]>("/inventory"));
    } catch { localStorage.removeItem("orderflow_access"); }
  }

  useEffect(() => {
    loadProducts().catch((reason: Error) => setError(reason.message));
    loadSession().catch((reason: Error) => setError(reason.message));
    const onHash = () => setPage((location.hash.slice(1) as Page) || "home");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => loadProducts().catch((reason: Error) => setError(reason.message)), 250);
    return () => clearTimeout(timer);
  }, [search, category, sort]);

  async function logout() {
    try { await request("/auth/logout", { method: "POST" }); } catch { /* local session cleanup still applies */ }
    localStorage.removeItem("orderflow_access");
    setUser(null); setOrders([]); setInventory([]); setDashboard(null); setMenuOpen(false);
    setNotice("You have been signed out.");
    navigate("home");
  }

  function addToCart(product: Product) {
    setCart({ ...cart, [product.id]: (cart[product.id] ?? 0) + 1 });
    setNotice(`${product.name} added to cart.`);
  }

  async function checkout() {
    if (!user) { setAuthOpen(true); return; }
    try {
      const order = await request<Order>("/orders", {
        method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ items: cartItems.map((product) => ({ product_id: product.id, quantity: cart[product.id] })) }),
      });
      await request("/payments", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ order_id: order.id, outcome: "success" }) });
      setCart({}); setOrders([order, ...orders]); setNotice("Order placed and payment simulated successfully."); navigate("orders");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Checkout failed"); }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="container navbar-inner">
        <button className="brand" onClick={() => navigate("home")}><span className="brand-mark">OF</span><strong>OrderFlow</strong></button>
        <nav className="public-nav">{(["home", "catalogue", "orders", "operations"] as const).map((item) => <button className={page === item ? "active" : ""} key={item} onClick={() => navigate(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}</nav>
        <div className="top-actions"><button className="icon-btn" onClick={() => navigate("cart")} aria-label="Cart"><ShoppingCart size={18} /><span className="cart-count" data-empty={Object.keys(cart).length === 0}>{Object.keys(cart).length}</span></button>{user ? <div className="account-wrap"><button className="profile" onClick={() => setMenuOpen(!menuOpen)}><span className="avatar">{user.first_name[0]}</span>{user.first_name}<ChevronDown size={15} /></button>{menuOpen && <div className="account-menu"><strong>{user.first_name} {user.last_name}</strong><small>{user.roles.join(" · ")}</small><button onClick={logout}><LogOut size={15} /> Log out</button></div>}</div> : <button className="primary compact" onClick={() => setAuthOpen(true)}>Sign in</button>}</div>
        </div>
      </header>
      {user && page !== "home" && <aside className={`sidebar ${sidebar ? "" : "collapsed"}`}><button className="sidebar-toggle" aria-label={sidebar ? "Collapse sidebar" : "Expand sidebar"} onClick={() => setSidebar(!sidebar)}>{sidebar ? <X size={17} /> : <Menu size={17} />}</button>{sidebar && <><p className="side-label">WORKSPACE</p><SideLink icon={<Home size={17} />} label="Overview" active={page === "operations"} onClick={() => navigate("operations")} /><SideLink icon={<Package size={17} />} label="Products" active={page === "catalogue"} onClick={() => navigate("catalogue")} /><SideLink icon={<Truck size={17} />} label="Orders" active={page === "orders"} onClick={() => navigate("orders")} /><SideLink icon={<Boxes size={17} />} label="Inventory" active={page === "inventory"} onClick={() => navigate("inventory")} /><SideLink icon={<Users size={17} />} label="Customers" onClick={() => setNotice("Customer management is available to administrators through the API.")} /><SideLink icon={<BarChart3 size={17} />} label="Analytics" active={page === "operations"} onClick={() => navigate("operations")} /></>}</aside>}
      <main className={user && page !== "home" ? "with-sidebar" : ""}>
        {(error || notice) && <div className={error ? "alert" : "notice"}>{error || notice}<button onClick={() => { setError(""); setNotice(""); }}>Dismiss</button></div>}
        {page === "home" && <HomePage navigate={navigate} products={products.slice(0, 4)} addToCart={addToCart} />}
        {page === "catalogue" && <Catalogue products={products} categories={categories} search={search} setSearch={setSearch} category={category} setCategory={setCategory} sort={sort} setSort={setSort} addToCart={addToCart} />}
        {page === "cart" && <Cart products={cartItems} cart={cart} setCart={setCart} total={total} checkout={checkout} navigate={navigate} />}
        {page === "orders" && <Orders orders={orders} user={user} />}
        {page === "operations" && <Operations dashboard={dashboard} orders={orders} />}
        {page === "inventory" && <InventoryView inventory={inventory} products={products} />}
      </main>
      <footer><div className="container">OrderFlow <span>Commerce operations, beautifully connected.</span></div></footer>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onLogin={(next) => { setUser(next); setAuthOpen(false); loadSession(); }} />}
    </div>
  );
}

function SideLink({ icon, label, active, onClick }: { icon: JSX.Element; label: string; active?: boolean; onClick: () => void }) {
  return <button className={`side-link ${active ? "active" : ""}`} onClick={onClick}>{icon}<span>{label}</span></button>;
}

function HomePage({ navigate, products, addToCart }: { navigate: (page: Page) => void; products: Product[]; addToCart: (product: Product) => void }) {
  return <><section className="hero"><div className="container hero-grid"><div><p className="eyebrow">THE OPERATING SYSTEM FOR MODERN COMMERCE</p><h1>Every order.<br /><span>Moving forward.</span></h1><p className="hero-copy">OrderFlow brings your catalogue, inventory, and fulfilment teams into one intelligent workspace.</p><div className="hero-actions"><button className="primary" onClick={() => navigate("catalogue")}>Explore catalogue <ShoppingBag size={17} /></button><button className="secondary" onClick={() => navigate("operations")}>See operations <BarChart3 size={17} /></button></div></div><div className="hero-visual"><div className="visual-top"><Sparkles size={16} /> LIVE OPERATIONS</div><div className="visual-chart"><span style={{ height: "35%" }} /><span style={{ height: "58%" }} /><span style={{ height: "46%" }} /><span style={{ height: "80%" }} /><span style={{ height: "68%" }} /><span style={{ height: "93%" }} /></div><div className="visual-total"><small>Revenue this month</small><strong>$84,290.40</strong><em>+18.4%</em></div></div></div></section><section className="feature-strip"><div className="container feature-grid"><div><strong>55+</strong><span>Curated products</span></div><div><strong>99.8%</strong><span>Stock accuracy</span></div><div><strong>24/7</strong><span>Order visibility</span></div><div><strong>1</strong><span>Connected workspace</span></div></div></section><section className="home-section container"><div className="section-heading"><div><p className="eyebrow">FEATURED COLLECTION</p><h2>Built for momentum</h2></div><button className="text-button" onClick={() => navigate("catalogue")}>View all products →</button></div><div className="product-grid">{products.map((product) => <ProductCard key={product.id} product={product} addToCart={addToCart} />)}</div></section></>;
}

function Catalogue({ products, categories, search, setSearch, category, setCategory, sort, setSort, addToCart }: { products: Product[]; categories: string[]; search: string; setSearch: (value: string) => void; category: string; setCategory: (value: string) => void; sort: string; setSort: (value: string) => void; addToCart: (product: Product) => void }) {
  return <section className="page-section container"><div className="page-heading"><div><p className="eyebrow">CATALOGUE</p><h1>Explore products</h1><p>Everything your operation needs, selected with intent.</p></div><div className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products..." /></div></div><div className="toolbar"><div className="chips"><button className={!category ? "selected" : ""} onClick={() => setCategory("")}>All</button>{categories.map((item) => <button className={category === item ? "selected" : ""} key={item} onClick={() => setCategory(item)}>{item}</button>)}</div><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="created_at">Newest first</option><option value="price">Price</option></select></div><div className="product-grid catalogue-grid">{products.map((product) => <ProductCard key={product.id} product={product} addToCart={addToCart} />)}</div></section>;
}

function ProductCard({ product, addToCart }: { product: Product; addToCart: (product: Product) => void }) {
  return <article className="product-card"><div className="product-art">{product.image_url ? <img src={product.image_url} alt={product.name} loading="lazy" onError={(event) => { event.currentTarget.style.display = "none"; }} /> : <span>{product.category.slice(0, 2).toUpperCase()}</span>}<span className="category-badge">{product.category}</span></div><div className="product-info"><small className="muted">{product.sku}</small><h3>{product.name}</h3><p className="muted">{product.description ?? "Designed for modern operations."}</p><div className="product-bottom"><strong>${Number(product.price).toFixed(2)}</strong><button className="add-btn" disabled={!product.available_quantity} onClick={() => addToCart(product)}>{product.available_quantity ? "Add to cart" : "Out of stock"}</button></div></div></article>;
}

function Cart({ products, cart, setCart, total, checkout, navigate }: { products: Product[]; cart: Record<string, number>; setCart: (cart: Record<string, number>) => void; total: number; checkout: () => void; navigate: (page: Page) => void }) {
  const tax = total * 0.08;
  return <section className="page-section narrow container"><div className="page-heading"><div><p className="eyebrow">CHECKOUT</p><h1>Your cart</h1><p>Review your items before placing your simulated order.</p></div></div>{products.length === 0 ? <div className="empty-state"><ShoppingCart size={30} /><h2>Your cart is empty</h2><p>Add products from the catalogue to get started.</p><button className="primary" onClick={() => navigate("catalogue")}>Continue shopping</button></div> : <div className="checkout-layout"><div className="cart-list">{products.map((product) => <div className="cart-row large" key={product.id}><img src={product.image_url} alt={product.name} /><div><strong>{product.name}</strong><small>{product.category}</small></div><div className="quantity"><button aria-label={`Decrease ${product.name} quantity`} onClick={() => setCart({ ...cart, [product.id]: Math.max(0, cart[product.id] - 1) })}>−</button><span>{cart[product.id]}</span><button aria-label={`Increase ${product.name} quantity`} onClick={() => setCart({ ...cart, [product.id]: cart[product.id] + 1 })}>+</button></div><strong>${(Number(product.price) * cart[product.id]).toFixed(2)}</strong></div>)}</div><aside className="summary"><h2>Order summary</h2><div><span>Subtotal</span><strong>${total.toFixed(2)}</strong></div><div><span>Tax</span><strong>${tax.toFixed(2)}</strong></div><div><span>Shipping</span><strong>Free</strong></div><hr /><div className="summary-total"><span>Total</span><strong>${(total + tax).toFixed(2)}</strong></div><button className="primary full" onClick={checkout}>Place simulated order</button></aside></div>}</section>;
}

function Orders({ orders, user }: { orders: Order[]; user: User | null }) {
  const counts = { total: orders.length, pending: orders.filter((order) => order.status === "PENDING").length, complete: orders.filter((order) => order.status === "DELIVERED").length };
  return <section className="page-section container"><div className="page-heading"><div><p className="eyebrow">ORDER MANAGEMENT</p><h1>{user ? "Your orders" : "Orders, in motion"}</h1><p>{user ? "Track every purchase from confirmation to delivery." : "Sign in to see your personal order history."}</p></div></div>{user ? <><div className="metric-grid"><Metric label="Total orders" value={counts.total} icon={<ShoppingBag />} /><Metric label="Pending" value={counts.pending} icon={<Truck />} /><Metric label="Completed" value={counts.complete} icon={<Sparkles />} /></div><div className="table-card"><div className="table-head"><strong>Recent orders</strong><span>Status</span><span>Total</span></div>{orders.length ? orders.map((order) => <div className="table-row" key={order.id}><strong>#{order.id.slice(0, 8)}</strong><span className={`status ${order.status.toLowerCase()}`}>{order.status}</span><strong>${Number(order.total).toFixed(2)}</strong></div>) : <div className="empty-state"><p>No orders yet.</p></div>}</div></> : <div className="empty-state"><ShoppingBag size={30} /><h2>Sign in to view orders</h2></div>}</section>;
}

function Operations({ dashboard, orders }: { dashboard: Record<string, number | string> | null; orders: Order[] }) {
  return <section className="page-section container"><div className="page-heading"><div><p className="eyebrow">OPERATIONS CENTER</p><h1>Good morning, operator.</h1><p>One clear view of your commerce performance.</p></div><div className="date-pill">Live data · Today</div></div><div className="metric-grid"><Metric label="Total revenue" value={dashboard ? `$${Number(dashboard.total_revenue).toLocaleString()}` : "$—"} icon={<BarChart3 />} /><Metric label="Total orders" value={dashboard?.total_orders ?? orders.length} icon={<ShoppingBag />} /><Metric label="Customers" value={dashboard?.total_customers ?? "—"} icon={<Users />} /><Metric label="Low stock" value={dashboard?.low_stock_products ?? "—"} icon={<Boxes />} /></div><div className="dashboard-grid"><div className="chart-card"><div className="card-title"><div><p className="eyebrow">REVENUE PULSE</p><h2>Performance overview</h2></div><span className="trend">+18.4%</span></div><div className="big-chart"><span style={{ height: "28%" }} /><span style={{ height: "45%" }} /><span style={{ height: "38%" }} /><span style={{ height: "66%" }} /><span style={{ height: "55%" }} /><span style={{ height: "82%" }} /><span style={{ height: "74%" }} /><span style={{ height: "96%" }} /></div></div><div className="chart-card insight"><Sparkles size={22} /><p className="eyebrow">INSIGHT</p><h2>Operations are trending up.</h2><p>Keep an eye on low-stock products to protect this week's momentum.</p></div></div></section>;
}

function Metric({ label, value, icon }: { label: string; value: string | number; icon: JSX.Element }) { return <div className="metric-card"><span className="metric-icon">{icon}</span><small>{label}</small><strong>{value}</strong><em>Live from your workspace</em></div>; }

function InventoryView({ inventory, products }: { inventory: Inventory[]; products: Product[] }) {
  const byId = new Map(products.map((product) => [product.id, product]));
  return <section className="page-section container"><div className="page-heading"><div><p className="eyebrow">INVENTORY CONTROL</p><h1>Stock, under control.</h1><p>Know what is available, reserved, and ready to move.</p></div></div><div className="metric-grid"><Metric label="Total stock" value={inventory.reduce((sum, item) => sum + item.quantity, 0)} icon={<Boxes />} /><Metric label="Available" value={inventory.reduce((sum, item) => sum + item.available_quantity, 0)} icon={<Package />} /><Metric label="Reserved" value={inventory.reduce((sum, item) => sum + item.reserved_quantity, 0)} icon={<Truck />} /></div><div className="table-card"><div className="table-head"><strong>Inventory overview</strong><span>Available</span><span>Status</span></div>{inventory.map((item) => <div className="table-row" key={item.product_id}><strong>{byId.get(item.product_id)?.name ?? item.product_id.slice(0, 8)}</strong><span>{item.available_quantity} units</span><span className={`status ${item.available_quantity <= item.low_stock_threshold ? "pending" : "delivered"}`}>{item.available_quantity <= item.low_stock_threshold ? "Low stock" : "Healthy"}</span></div>)}</div></section>;
}

function AuthModal({ onClose, onLogin }: { onClose: () => void; onLogin: (user: User) => void }) {
  const [register, setRegister] = useState(false); const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [confirm, setConfirm] = useState(""); const [first, setFirst] = useState(""); const [last, setLast] = useState(""); const [error, setError] = useState(""); const [visible, setVisible] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); try { if (register) { if (password !== confirm) throw new Error("Passwords do not match"); await request("/auth/register", { method: "POST", body: JSON.stringify({ email, password, first_name: first, last_name: last }) }); } const tokens = await request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); localStorage.setItem("orderflow_access", tokens.access_token); onLogin(await request<User>("/auth/me")); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to authenticate"); } }
  return <div className="modal-backdrop" role="dialog" aria-modal="true" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><form className="modal" onSubmit={submit}><button className="close" type="button" aria-label="Close dialog" onClick={onClose}><X size={18} /></button><p className="eyebrow">{register ? "CREATE YOUR WORKSPACE" : "WELCOME BACK"}</p><h2>{register ? "Create your account" : "Sign in to OrderFlow"}</h2>{error && <div className="alert">{error}</div>}{register && <div className="name-fields"><label>First name<input required value={first} onChange={(event) => setFirst(event.target.value)} /></label><label>Last name<input required value={last} onChange={(event) => setLast(event.target.value)} /></label></div>}<label>Email<input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label><label>Password<div className="password-field"><input type={visible ? "text" : "password"} minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} /><button type="button" onClick={() => setVisible(!visible)}>{visible ? "Hide" : "Show"}</button></div></label>{register && <label>Confirm password<input type={visible ? "text" : "password"} required value={confirm} onChange={(event) => setConfirm(event.target.value)} /></label>}<button className="primary full">{register ? "Create account" : "Sign in"}</button><button className="text-button" type="button" onClick={() => { setRegister(!register); setError(""); }}>{register ? "Already have an account? Sign in" : "New here? Create an account"}</button></form></div>;
}

createRoot(document.getElementById("root")!).render(<App />);
