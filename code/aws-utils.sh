#!/bin/bash
#
# Usage: source aws-utils.sh

SOURCE="${BASH_SOURCE[0]:-$0}"
DIR="$( cd "$( dirname "$SOURCE" )" && pwd )"

alias ec2="invoke -c ec2-tasks -r $DIR/code"

complete -C aws_completer aws
