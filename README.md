# miniraven

**Rabennest** a.k.a. **miniraven** is a tool meant to assist in bringing up Ravenports on new platforms that do not yet have a bootstrap package available.

## Why?

[Ravenports](http://www.ravenports.com "Ravenports official website") is a sophisticated package system for Unix-like operating systems. It consists of package recipes (buildsheets), a packaging framework, a package manager and ready-to-use package repositories. RP currently supports **DragonFly BSD**, **FreeBSD**, **Linux** and **Solaris** on **amd64**.

Creating software packages and maintaining them over time is not a trivial task. While designed to be both highly efficient and easy to use, RP pays for these traits with a certain complexity. And while the latter is hidden from the end-user, bringing the framework up on a new platform is not for the faint-hearted. It is a process involving multiple steps, some of which are not that hard but boring and time-consuming. This project aims at scripting some tasks that can be automated easily.

## Status

Rabennest does only run on the reference platform (FreeBSD amd64) at the moment. It can almost build all three of the main non-Ada components: Customized **bmake** and the **fake-uname** work. All requirements for the **ravensw** package manager are also built, but ravensw itself errors out right now. This needs to be investigated.

I'm making this project public now because it could help others who would like to try getting RP to work on a platform not supported yet.

My plan is to start documenting functions. When that is done some refactoring - including splitting up the configuration to separate general configuration and package information - is in order. And then data to handle more platforms correctly should be added (as well as perhaps some additional features).

## History

This is my second attempt at writing a tool that helps in getting Ravenports on any system from zero to working. The first one was a single Python script (ok, in fact I tried it with plain shell scripting first, but that was even more ugly...) that built all non-Ada parts on a couple of platforms. This was before the Ravensw package manager was introduced, though. Also it was a complete mess, so I decided to start over from scratch.

The new version uses a config file to separate package information from the actual program among other things. It's quite a bit cleaner and making use of modules now, but I won't deny that it could use a lot of refactoring as well...
