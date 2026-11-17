// CDK app entry: npx cdk synth -c env=dev -c imageTag=v2.4.0  (synth is offline in this exercise)
import { App } from "aws-cdk-lib";
import { buildApp } from "../lib/app";

const app = new App();
buildApp(app);
