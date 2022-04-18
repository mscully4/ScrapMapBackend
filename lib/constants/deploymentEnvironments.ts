import { DeploymentEnvironment } from "../types/DeploymentEnvironment";
import { awsAccounts } from "./accounts";
import { stages } from "./stages";

export const deploymentEnvironments: Array<DeploymentEnvironment> = [
  {
    stage: stages.BETA,
    account: awsAccounts[stages.BETA],
    region: "us-west-2"
  }
]