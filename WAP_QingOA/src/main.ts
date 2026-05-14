import { createApp } from "vue";
import App from "./App.vue";
import { setPageTitle } from "./pageTitle";
import { router } from "./router";
import "./styles.css";

router.afterEach((to) => {
  const routeTitle = typeof to.meta.title === "string" ? to.meta.title : undefined;
  setPageTitle(routeTitle);
});

createApp(App).use(router).mount("#app");
