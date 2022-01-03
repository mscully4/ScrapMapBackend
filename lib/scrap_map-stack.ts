import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ApiStack } from './stacks/apiStack'
import { UserPoolStack } from './stacks/userPoolStack';

const env = {
  account: "735029168602",
  region: "us-west-2"
}

export class ScrapMapStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, {...props, env});

    const userPoolStack = new UserPoolStack(this, 'userPoolStack', {
      env: env
    })

    const apiStack = new ApiStack(this, 'apiStack', {
      env: env,
      userPool: userPoolStack.userPool,
      clientId: userPoolStack.userPoolClient.userPoolClientId,
      userPoolRole: userPoolStack.userPoolRole
    })
  }
}
