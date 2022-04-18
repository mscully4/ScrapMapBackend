import { App } from "aws-cdk-lib";
import { deploymentEnvironments } from "./constants/deploymentEnvironments";
import { ApiStack } from "./stacks/apiStack";
import { StorageStack } from "./stacks/storageStack";
import { UserPoolStack } from "./stacks/userPoolStack";
import { DeploymentEnvironment } from "./types/DeploymentEnvironment";

const appName = "travelMap"
const app = new App();

deploymentEnvironments.forEach((env: DeploymentEnvironment) => {
  const storageStack = new StorageStack(app, `${appName}-storageStack`, {
    env: env,
  });

  const userPoolStack = new UserPoolStack(app, `${appName}-userPoolStack`, {
    env: env,
  });

  new ApiStack(app, `${appName}-apiStack`, {
    env: env,
    userPool: userPoolStack.userPool,
    clientId: userPoolStack.userPoolClient.userPoolClientId,
    userPoolRole: userPoolStack.userPoolRole,
    dynamoTableReadRole: storageStack.dynamoTableReadRole,
    dynamoTableWriteRole: storageStack.dynamoTableWriteRole,
    dynamoTableName: storageStack.dynamoTableName,
  });
});


