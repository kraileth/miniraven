# miniraven

**Rabennest** a.k.a. **miniraven** is a tool meant to assist in bringing up Ravenports on new platforms that do not yet have a bootstrap package available.

## Why?

[Ravenports](www.ravenports.com "Ravenports official website") is a sophisticated package system for Unix-like operating systems. It consists of package recipes (buildsheets), a packaging framework, a package manager and ready-to-use package repositories. RP currently supports **DragonFly BSD**, **FreeBSD**, **Linux** and **Solaris** on **amd64**.

Creating software packages and maintaining them over time is not a trivial task. While designed to be both highly efficient and easy to use, RP pays for these traits with a certain complexity. And while the latter is hidden from the end-user, bringing the framework up on a new platform is not for the faint-hearted. It is a process involving multiple steps, some of which are not that hard but boring and time-consuming. This project aims at scripting some tasks that can be automated easily.

## Status

Rabennest does only run on the reference platform (FreeBSD amd64) at the moment. It can almost build all three of the main non-Ada components: Customized **bmake** and the **fake-uname** work. All requirements for the **ravensw** package manager are also built, but ravensw itself errors out right now. This needs to be investigated.

I'm making this project public now because it could help others who would like to try getting RP to work on a not yet supported platform. My plan is to split it up into several modules next and to start documenting things. When that is done some refactoring is in order. And then data to handle more platforms correctly should be added (as well as perhaps some convenience features).

## History

This is my second attempt at writing a tools that helps in getting Ravenports on any system from zero to working. The first one was a single Python script that did build all non-Ada parts on a couple of platforms. This was before the Ravensw package manager was introduced, though. Also it was a complete mess, so I decided to start over from scratch. The new version uses a config file to separate package information from the actual program among other things. It's quite a bit cleaner, but I won't deny that it could use a lot of refactoring as well...
