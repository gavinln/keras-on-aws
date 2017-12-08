# keras-on-aws

* Source code - [Github][1]
* Author - Gavin Noronha - <gnoronha@hotmail.com>

[1]: https://github.com/gavinln/keras-on-aws.git

## About

This project provides an [Ubuntu (16.04)][10] [Vagrant][20] Virtual Machine
(VM) with the [TensorFlow][30] library from Google. It also includes the
[Keras][40] library built on TensorFlow. [Jupyter][50] notebooks are installed
to make it easy to run the code.

[10]: http://releases.ubuntu.com/16.04/
[20]: http://www.vagrantup.com/
[30]: http://tensorflow.org/
[40]: https://github.com/fchollet/keras
[50]: http://jupyter.org/

Follow the **Requirements** section below for a one-time setup of Virtualbox,
Vagrant and Git before running the commands below. These instructions should
work on Windows, Mac and Linux operating systems.

## Running Keras

### 1. Start the VM

1. Change to the keras-on-aws root directory

    ```
    cd keras-on-aws
    ```

2. Create a do_not_checkin directory ignored by Git. You AWS credentials
will go here

    ```
    mkdir do_not_checkin
    ```

3. Make sure you have a new verion of Vagrant (1.9.1 or higher)

    ```
    vagrant -v
    ```

4. Start the Virtual machine (VM)

    ```
    vagrant up
    ```

5. Login to the VM

    ```
    vagrant ssh
    ```

## Requirements

The following software is needed to get the software from github and run
Vagrant. The Git environment also provides an [SSH client][200] for Windows.

* [Oracle VM VirtualBox][210]
* [Vagrant][220] version 1.9.1 or higher
* [Git][230]

[200]: http://en.wikipedia.org/wiki/Secure_Shell
[210]: https://www.virtualbox.org/
[220]: http://vagrantup.com/
[230]: http://git-scm.com/
